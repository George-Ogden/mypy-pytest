from collections import deque
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import functools
import itertools
from typing import cast

import _pytest.config
from _pytest.fixtures import FixtureManager as PytestFixtureManager
from _pytest.main import Session
from mypy.checker import TypeChecker
from mypy.nodes import MypyFile
from mypy.types import CallableType, Instance, LiteralType, Type, UnionType
from pytest import FixtureDef

from .checker_wrapper import CheckerWrapper
from .fixture import Fixture, FixtureScope
from .fullname import Fullname
from .types_module import TYPES_MODULE
from .utils import extract_singleton, filter_unique, strict_cast, strict_not_none


@dataclass(frozen=True, slots=True)
class FixtureManager(CheckerWrapper):
    checker: TypeChecker

    @classmethod
    def conftest_names(cls, name: Fullname) -> Iterable[Fullname]:
        while name:
            name = name.module_name
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
        config.parse(["-s", "--fixtures"])

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

    @filter_unique
    def autouse_fixture_names(self, test_module: Fullname) -> Iterable[str]:
        for module_name in itertools.chain(
            self.resolution_sequence(test_module), self.default_fixture_module_names()
        ):
            module = self.checker.modules.get(str(module_name))
            if module is not None:
                yield from self.autouse_fixture_names_from_module(module)

    @classmethod
    def autouse_fixture_names_from_module(cls, module: MypyFile) -> Sequence[str]:
        autouse_node = module.names.get(Fixture.AUTOUSE_NAME)
        if autouse_node is None:
            return []
        assert autouse_node.type is not None
        return cls.autouse_fixture_names_from_type(strict_not_none(autouse_node.type))

    @classmethod
    def autouse_fixture_names_from_type(cls, type_: Type) -> Sequence[str]:
        match type_:
            case UnionType():
                return [
                    extract_singleton(cls.autouse_fixture_names_from_type(type_))
                    for type_ in type_.items
                ]
            case LiteralType():
                return [strict_cast(str, type_.value)]
        raise TypeError()

    def resolve_fixtures(
        self, request_names: Sequence[str], test_module: Fullname
    ) -> Mapping[str, Sequence[Fixture]]:
        unresolved_fixtures = deque(
            itertools.chain(request_names, self.autouse_fixture_names(test_module))
        )
        fixtures: dict[str, list[Fixture]] = {}
        while unresolved_fixtures:
            fixture_name = unresolved_fixtures.popleft()
            if fixture_name not in fixtures:
                fixtures[fixture_name] = self.resolve_fixture(fixture_name, test_module)
                for fixture in fixtures[fixture_name]:
                    unresolved_fixtures.extend(argument.name for argument in fixture.arguments)
        return fixtures

    @functools.lru_cache  # noqa: B019
    def resolve_fixture(self, request_name: str, test_module: Fullname) -> list[Fixture]:
        fixtures = []
        for module_name in self.resolution_sequence(test_module):
            module_fullname: str | None = str(module_name) if module_name else None
            try:
                module = None if module_fullname is None else self.checker.modules[module_fullname]
            except KeyError:
                continue
            fixture: Fixture | None = self.lookup_or_none(module, request_name)
            if fixture is not None:
                fixtures.append(fixture)
        return fixtures

    def lookup_or_none(self, module: MypyFile | None, request_name: str) -> Fixture | None:
        if module is None:
            return self._default_lookup(request_name)
        return self._module_lookup(module, request_name)

    def _module_lookup(self, module: MypyFile, request_name: str) -> Fixture | None:
        decorator = module.names.get(request_name)
        if (
            decorator is not None
            and isinstance(type_ := decorator.type, Instance)
            and type_.type.fullname == f"{TYPES_MODULE}.fixture_type.FixtureType"
        ):
            [scope, signature, is_generator, fullname, autouse] = type_.args
            assert isinstance(scope, LiteralType)
            assert isinstance(signature, CallableType)
            assert isinstance(is_generator, LiteralType)
            assert isinstance(fullname, LiteralType)
            assert isinstance(autouse, LiteralType)
            return Fixture.from_type(
                signature,
                scope=cast(FixtureScope, scope.value),
                autouse=cast(bool, autouse.value),
                file=module.path,
                is_generator=cast(bool, is_generator.value),
                fullname=cast(str, fullname.value),
            )
        return None

    def _default_lookup(self, request_name: str) -> Fixture | None:
        for module_fullname in map(str, self.default_fixture_module_names()):
            if module_fullname in self.checker.modules:
                fixture = self._module_lookup(self.checker.modules[module_fullname], request_name)
                if fixture is not None:
                    return fixture
        return None
