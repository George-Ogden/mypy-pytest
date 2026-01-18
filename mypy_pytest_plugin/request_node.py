from __future__ import annotations

from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass
from typing import Literal, Self

from mypy.checker import TypeChecker
from mypy.nodes import Context
from mypy.types import Type, TypeVarLikeType

from .fixture import Fixture, FixtureScope
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .request import Request


@dataclass(slots=True)
class RequestNode:
    request: Request
    _: KW_ONLY
    file: str
    source: Literal["argument", "fixture", "autouse"]
    source_name: str
    resolver: Fixture | None | Literal["param"] = None
    scope: FixtureScope = FixtureScope.function

    @classmethod
    def from_autouse_name(cls, name: str, module: Fullname, checker: TypeChecker) -> Self:
        for fixture in FixtureManager(checker).resolve_fixture(name, module):
            if fixture.autouse:
                return cls.from_autouse(fixture)
        raise AssertionError()

    @classmethod
    def from_autouse(cls, fixture: Fixture) -> Self:
        request = cls(
            fixture.as_argument(), file=fixture.file, source="autouse", source_name=fixture.name
        )
        return request

    @property
    def name(self) -> str:
        return self.request.name

    @property
    def type_(self) -> Type:
        return self.request.type_

    @property
    def context(self) -> Context:
        return self.request.context

    @property
    def type_variables(self) -> Sequence[TypeVarLikeType]:
        return self.request.type_variables
