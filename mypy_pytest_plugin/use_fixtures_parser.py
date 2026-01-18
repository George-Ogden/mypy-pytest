from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import functools
from typing import ClassVar

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Expression
from mypy.types import AnyType, Instance, TypeOfAny

from .checker_wrapper import CheckerWrapper
from .defer import DeferralError, DeferralReason
from .names_parser import NamesParser
from .request import Request
from .use_fixture_names_parser import UseFixtureNamesParser


@dataclass(frozen=True)
class UseFixturesParser(CheckerWrapper):
    checker: TypeChecker
    USE_FIXTURES_TYPE_FULLNAME: ClassVar[str] = "_pytest.mark.structures._UsefixturesMarkDecorator"

    @classmethod
    def use_fixture_requests(
        cls, decorators: Iterable[Expression], checker: TypeChecker
    ) -> list[Request]:
        return list(UseFixturesParser(checker).requests_from_decorators(decorators))

    def requests_from_decorators(self, decorators: Iterable[Expression]) -> Iterable[Request]:
        for decorator in decorators:
            yield from self.requests_from_decorator(decorator)

    def requests_from_decorator(self, decorator: Expression) -> Iterable[Request]:
        if isinstance(decorator, CallExpr):
            return self.requests_from_call(decorator)
        return []

    def requests_from_call(self, call: CallExpr) -> Iterable[Request]:
        type_ = self.checker.lookup_type_or_none(call.callee)
        if type_ is None:
            raise DeferralError(DeferralReason.REQUIRED_WAIT)
        if isinstance(type_, Instance) and type_.type.fullname == self.USE_FIXTURES_TYPE_FULLNAME:
            return self.requests_from_call_args(call.args)
        return []

    def requests_from_call_args(self, args: Sequence[Expression]) -> Iterable[Request]:
        for arg in args:
            if (request := self.request_from_arg(arg)) is not None:
                yield request

    def request_from_arg(self, arg: Expression) -> Request | None:
        if (name := self.name_parser.parse_name(arg)) is None:
            return None
        return Request(
            name=name, type_=AnyType(TypeOfAny.unannotated), type_variables=[], context=arg
        )

    @functools.cached_property
    def name_parser(self) -> NamesParser:
        return UseFixtureNamesParser(self.checker)
