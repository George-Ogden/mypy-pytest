from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import ClassVar

from mypy.checker import TypeChecker
from mypy.nodes import Expression
from mypy.types import AnyType, Instance, LiteralType, Type, TypeOfAny, UnionType

from .checker_wrapper import CheckerWrapper
from .request import Request
from .types_module import TYPES_MODULE


@dataclass(frozen=True)
class UsingFixturesParser(CheckerWrapper):
    checker: TypeChecker
    USING_FIXTURES_TYPE_FULLNAME: ClassVar[str] = (
        f"{TYPES_MODULE}.pytest._UsingFixturesMarkDecorator"
    )

    @classmethod
    def use_fixture_requests(
        cls, decorators: Iterable[Expression], checker: TypeChecker
    ) -> list[Request]:
        return list(UsingFixturesParser(checker).requests_from_decorators(decorators))

    def requests_from_decorators(self, decorators: Iterable[Expression]) -> Iterable[Request]:
        for decorator in decorators:
            yield from self.requests_from_decorator(decorator)

    def requests_from_decorator(self, decorator: Expression) -> Iterable[Request]:
        return self.requests_from_type(self.checker.lookup_type(decorator))

    def requests_from_type(self, type_: Type) -> Iterable[Request]:
        if isinstance(type_, Instance) and type_.type.fullname == self.USING_FIXTURES_TYPE_FULLNAME:
            return self.requests_from_type_args(type_.args)
        return []

    def requests_from_type_args(self, type_args: Sequence[Type]) -> Iterable[Request]:
        [type_arg] = type_args
        return self.requests_from_type_arg(type_arg)

    def requests_from_type_arg(self, type_: Type) -> Iterable[Request]:
        assert isinstance(type_, UnionType)
        return self.requests_from_type_items(type_.items)

    def requests_from_type_items(self, types: Sequence[Type]) -> Iterable[Request]:
        for type_ in types:
            assert isinstance(type_, LiteralType)
            yield self.request_from_type_item(type_)

    def request_from_type_item(self, type_: LiteralType) -> Request:
        assert isinstance(type_.value, str)
        return Request(
            name=type_.value, type_=AnyType(TypeOfAny.unannotated), type_variables=[], context=type_
        )
