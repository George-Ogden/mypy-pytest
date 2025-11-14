from collections.abc import Sequence
from dataclasses import dataclass
import enum
from typing import Final, Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Context, Decorator, Expression
from mypy.types import CallableType, Instance, LiteralType, Overloaded, Type

from .error_codes import DUPLICATE_FIXTURE, INVALID_FIXTURE_SCOPE
from .fullname import Fullname
from .test_argument import TestArgument

FixtureScope = enum.IntEnum("FixtureScope", ["function", "class", "module", "package", "session"])
DEFAULT_SCOPE: Final[FixtureScope] = FixtureScope.function


@dataclass(frozen=True, slots=True, kw_only=True)
class Fixture:
    fullname: Fullname
    return_type: Type
    arguments: Sequence[TestArgument]
    scope: FixtureScope
    context: Context

    @classmethod
    def from_decorator(cls, decorator: Decorator, checker: TypeChecker) -> Self | None:
        fixture_decorator = cls.fixture_decorator(decorator.decorators, checker)
        arguments = TestArgument.from_fn_def(decorator.func, checker=checker)
        if fixture_decorator is None or arguments is None:
            return None
        return cls(
            fullname=Fullname(decorator.fullname),
            return_type=cast(CallableType, decorator.func.type).ret_type,
            arguments=arguments,
            scope=cls._fixture_scope_from_decorator(fixture_decorator, checker),
            context=decorator.func,
        )

    def as_argument(self) -> TestArgument:
        return TestArgument(name=self.fullname.back, type_=self.return_type, context=self.context)

    @classmethod
    def fixture_decorator(
        cls, decorators: Sequence[Expression], checker: TypeChecker
    ) -> Expression | None:
        fixture_decorators = [
            decorator for decorator in decorators if cls._is_fixture_decorator(decorator, checker)
        ]
        if len(fixture_decorators) == 1:
            [fixture_decorator] = fixture_decorators
            return fixture_decorator
        for decorator in fixture_decorators[:-1]:
            cls._warn_extra_decorator(decorator, checker)
        return None

    @classmethod
    def _warn_extra_decorator(cls, decorator: Expression, checker: TypeChecker) -> None:
        checker.fail(
            "Extra `pytest.fixture` decorator. Only one is allowed.",
            context=decorator,
            code=DUPLICATE_FIXTURE,
        )

    @classmethod
    def _is_fixture_decorator(cls, decorator: Expression, checker: TypeChecker) -> bool:
        decorator_type = checker.lookup_type(decorator)
        return cls._is_fixture_type(decorator_type) or (
            isinstance(decorator_type, Overloaded)
            and any(cls._is_fixture_type(overload.ret_type) for overload in decorator_type.items)
        )

    @classmethod
    def _is_fixture_type(cls, type_: Type) -> bool:
        return (
            isinstance(type_, Instance)
            and type_.type.fullname == "_pytest.fixtures.FixtureFunctionMarker"
        )

    @classmethod
    def _fixture_scope_from_decorator(
        cls, decorator: Expression, checker: TypeChecker
    ) -> FixtureScope:
        if isinstance(decorator, CallExpr):
            return cls._fixture_scope_from_call(decorator, checker)
        return DEFAULT_SCOPE

    @classmethod
    def _fixture_scope_from_call(cls, call: CallExpr, checker: TypeChecker) -> FixtureScope:
        scope_expressions = [
            arg for name, arg in zip(call.arg_names, call.args, strict=True) if name == "scope"
        ]
        if not scope_expressions:
            return DEFAULT_SCOPE
        [scope_expression] = scope_expressions
        return cls._fixture_scope_from_type(
            checker.lookup_type(scope_expression), checker=checker, context=scope_expression
        )

    @classmethod
    def _fixture_scope_from_type(
        cls, type_: Type, context: Expression, checker: TypeChecker
    ) -> FixtureScope:
        if isinstance(type_, LiteralType) and type_.value in FixtureScope._member_names_:
            return FixtureScope[cast(str, type_.value)]
        checker.fail("Invalid type for fixture scope.", context=context, code=INVALID_FIXTURE_SCOPE)

        return DEFAULT_SCOPE
