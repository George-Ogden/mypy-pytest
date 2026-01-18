from collections.abc import Sequence
from dataclasses import dataclass
import functools
from typing import ClassVar

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Expression
from mypy.types import Instance, LiteralType, UnionType

from .checker_wrapper import CheckerWrapper
from .names_parser import NamesParser
from .types_module import TYPES_MODULE
from .use_fixture_names_parser import UseFixtureNamesParser


@dataclass(frozen=True)
class UseFixturesParser(CheckerWrapper):
    checker: TypeChecker
    USING_FIXTURES_TYPE_NAME: ClassVar[str] = f"{TYPES_MODULE}._UsingFixturesMarkDecorator"

    @classmethod
    def type_for_usefixtures(cls, call: CallExpr, *, checker: TypeChecker) -> Instance:
        return cls(checker)._type_for_usefixtures(call)

    def _type_for_usefixtures(self, call: CallExpr) -> Instance:
        using_fixtures_type = self.checker.named_generic_type(
            self.USING_FIXTURES_TYPE_NAME,
            [self._type_for_usefixture_args(call.args)],
        )
        using_fixtures_type.set_line(call)
        return using_fixtures_type

    def _type_for_usefixture_args(self, args: Sequence[Expression]) -> UnionType:
        return UnionType(
            [
                arg_type
                for arg in args
                if (arg_type := self._type_for_usefixtures_argument(arg)) is not None
            ]
        )

    def _type_for_usefixtures_argument(self, arg: Expression) -> LiteralType | None:
        if (name := self.name_parser.parse_name(arg)) is None:
            return None
        name_type = LiteralType(name, self.checker.str_type())
        name_type.set_line(arg)
        return name_type

    @functools.cached_property
    def name_parser(self) -> NamesParser:
        return UseFixtureNamesParser(self.checker)
