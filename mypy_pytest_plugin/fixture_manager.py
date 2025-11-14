from collections.abc import Iterable, Sequence
import functools

import _pytest.config
from _pytest.fixtures import FixtureManager as PytestFixtureManager
from _pytest.main import Session
from pytest import FixtureDef  # noqa: PT013

from .fullname import Fullname


class FixtureManager:
    @classmethod
    def conftest_names(cls, name: Fullname) -> Iterable[Fullname]:
        while name:
            _, name = name.pop_back()
            yield name.push_back("conftest")

    @classmethod
    def full_resolution_sequence(cls, name: Fullname) -> Iterable[Fullname]:
        yield name
        yield from cls.conftest_names(name)
        if name:
            yield Fullname()

    @classmethod
    @functools.lru_cache
    def default_fixture_modules(cls) -> Sequence[Fullname]:
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
