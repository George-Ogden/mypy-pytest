from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import functools

import _pytest.config
from _pytest.fixtures import FixtureManager as PytestFixtureManager
from _pytest.main import Session
from mypy.checker import TypeChecker
from mypy.nodes import Decorator, MypyFile
from pytest import FixtureDef  # noqa: PT013

from .fixture import Fixture
from .fullname import Fullname
from .request import Request
from .test_argument import TestArgument


@dataclass(frozen=True, slots=True)
class FixtureManager:
    checker: TypeChecker

    @classmethod
    def conftest_names(cls, name: Fullname) -> Iterable[Fullname]:
        while name:
            _, name = name.pop_back()
            yield name.push_back("conftest")

    @classmethod
    def resolution_sequence(cls, name: Fullname) -> Iterable[Fullname]:
        yield name
        yield from cls.conftest_names(name)
        if name:
            yield Fullname(())

    @classmethod
    @functools.lru_cache
    def default_fixture_module_names(cls) -> Sequence[Fullname]:
        config = _pytest.config.get_config()
        config.parse(["-s", "--fixtures", "--noconftest"])

        session = Session.from_config(config)
        fixture_manager = PytestFixtureManager(session)
        return tuple(
            {
                cls._fixture_module(fixture_defs[-1])
                for fixture_defs in fixture_manager._arg2fixturedefs.values()
            }
        )

    @classmethod
    def _fixture_module(cls, fixture: FixtureDef) -> Fullname:
        return Fullname.from_string(fixture.func.__module__)

    def resolve_requests_and_fixtures(
        self, start: Sequence[TestArgument], module: Fullname
    ) -> tuple[dict[str, Request], list[Fixture]]:
        unresolved_requests = {
            argument.name: Request(argument, source="argument") for argument in start
        }
        resolved_requests: dict[str, Request] = {}
        fixtures: list[Fixture] = []
        for module_name in self.resolution_sequence(module):
            module_fullname: str | None = str(module_name) if module_name else None
            if module_fullname is None or module_fullname in self.checker.modules:
                fixtures.extend(
                    self.resolve_fixtures_at_module(
                        unresolved_requests,
                        resolved_requests,
                        module=None
                        if module_fullname is None
                        else self.checker.modules[module_fullname],
                    )
                )
        return resolved_requests | {
            name: argument for name, argument in unresolved_requests.items()
        }, fixtures

    def resolve_fixtures_at_module(
        self,
        unresolved: dict[str, Request],
        resolved: dict[str, Request],
        *,
        module: MypyFile | None,
    ) -> Iterable[Fixture]:
        maybe_resolved = deque(
            unresolved.pop(argument_name) for argument_name in list(unresolved.keys())
        )
        while maybe_resolved:
            request = maybe_resolved.popleft()
            if request.name in resolved.keys() or request.name in unresolved.keys():
                continue
            fixture: Fixture | None = self.lookup_or_none(module, request.name)
            if fixture is None:
                unresolved[request.name] = request
            else:
                resolved[request.name] = request
                yield fixture
                for argument in fixture.arguments:
                    maybe_resolved.append(Request(argument, source="fixture"))

    def lookup_or_none(self, module: MypyFile | None, request_name: str) -> Fixture | None:
        if module is None:
            return self._default_lookup(request_name)
        return self._module_lookup(module, request_name)

    def _module_lookup(self, module: MypyFile, request_name: str) -> Fixture | None:
        decorator = module.names.get(request_name)
        if decorator is not None and isinstance(decorator.node, Decorator):
            return Fixture.from_decorator(decorator.node, self.checker)
        return None

    def _default_lookup(self, request_name: str) -> Fixture | None:
        for module_fullname in map(str, self.default_fixture_module_names()):
            if module_fullname in self.checker.modules:
                fixture = self._module_lookup(self.checker.modules[module_fullname], request_name)
                if fixture is not None:
                    return fixture
        return None
