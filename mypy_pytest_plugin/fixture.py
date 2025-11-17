from collections.abc import Sequence
from dataclasses import dataclass
import enum
from pathlib import Path
from typing import Final, Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Context, Decorator, Expression, FuncDef
from mypy.subtypes import is_subtype
from mypy.types import CallableType, Instance, LiteralType, Overloaded, Type, TypeVarLikeType

from .defer import DeferralError
from .error_codes import DUPLICATE_FIXTURE, INVALID_FIXTURE_SCOPE, MARKED_FIXTURE
from .error_info import ExtendedContext
from .fullname import Fullname
from .logger import Logger
from .test_argument import TestArgument

FixtureScope = enum.IntEnum(
    "FixtureScope", ["function", "class", "module", "package", "session", "unknown"]
)
DEFAULT_SCOPE: Final[FixtureScope] = FixtureScope.function


@dataclass(frozen=True, slots=True, kw_only=True)
class Fixture:
    fullname: Fullname
    file: Path
    return_type: Type
    arguments: Sequence[TestArgument]
    scope: FixtureScope
    type_variables: Sequence[TypeVarLikeType]
    context: FuncDef

    @classmethod
    def from_decorator(cls, decorator: Decorator, checker: TypeChecker) -> Self | None:
        fixture_decorator = cls.fixture_decorator(decorator.decorators, checker)
        if fixture_decorator is None or cls._contains_mark_decorators(
            decorator.decorators, checker
        ):
            return None
        arguments = TestArgument.from_fn_def(decorator.func, checker=checker)
        if arguments is None:
            return None
        return cls(
            fullname=Fullname.from_string(decorator.fullname),
            file=ExtendedContext.checker_path(checker),
            return_type=cast(CallableType, decorator.func.type).ret_type,
            arguments=arguments,
            scope=cls._fixture_scope_from_decorator(fixture_decorator, checker),
            context=decorator.func,
            type_variables=decorator.func.type.variables
            if isinstance(decorator.func.type, CallableType)
            else [],
        )

    def as_argument(self) -> TestArgument:
        return TestArgument(
            name=self.fullname.back,
            type_=self.return_type,
            context=self.context,
            type_variables=self.type_variables,
        )

    @classmethod
    def is_fixture_and_mark(cls, decorator: Decorator, *, checker: TypeChecker) -> bool:
        return bool(
            cls.fixture_decorators(decorator.decorators, checker)
        ) and cls._contains_mark_decorators(decorator.decorators, checker)

    @classmethod
    def _contains_mark_decorators(cls, decorators: list[Expression], checker: TypeChecker) -> bool:
        return any([cls._is_mark(decorator, checker) for decorator in decorators])

    @classmethod
    def _is_mark(cls, expression: Expression, checker: TypeChecker) -> bool:
        if is_mark := is_subtype(
            checker.lookup_type(expression), checker.named_type("pytest.MarkDecorator")
        ):
            Logger.error(
                "Marks cannot be applied to fixtures.",
                context=ExtendedContext.from_context(expression, checker),
                code=MARKED_FIXTURE,
            )
        return is_mark

    @classmethod
    def fixture_decorator(
        cls, decorators: Sequence[Expression], checker: TypeChecker
    ) -> Expression | None:
        fixture_decorators = cls.fixture_decorators(decorators, checker)
        if len(fixture_decorators) == 1:
            [fixture_decorator] = fixture_decorators
            return fixture_decorator
        for decorator in fixture_decorators[1:]:
            cls._warn_extra_decorator(decorator, checker)
        return None

    @classmethod
    def fixture_decorators(
        cls, decorators: Sequence[Expression], checker: TypeChecker
    ) -> list[Expression]:
        return [
            decorator for decorator in decorators if cls._is_fixture_decorator(decorator, checker)
        ]

    @classmethod
    def _warn_extra_decorator(cls, decorator: Expression, checker: TypeChecker) -> None:
        Logger.error(
            "Extra `pytest.fixture` decorator. Only one is allowed.",
            context=ExtendedContext.from_context(decorator, checker),
            code=DUPLICATE_FIXTURE,
        )

    @classmethod
    def _is_fixture_decorator(cls, decorator: Expression, checker: TypeChecker) -> bool:
        decorator_type = checker.lookup_type_or_none(decorator)
        if decorator_type is None:
            raise DeferralError()
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
        cls, type_: Type, context: Context, checker: TypeChecker
    ) -> FixtureScope:
        if isinstance(type_, LiteralType) and type_.value in FixtureScope._member_names_:
            return FixtureScope[cast(str, type_.value)]
        Logger.error(
            "Invalid type for fixture scope.",
            context=ExtendedContext.from_context(context, checker),
            code=INVALID_FIXTURE_SCOPE,
        )

        return FixtureScope.unknown

    @property
    def name(self) -> str:
        return self.fullname.back

    @property
    def module_name(self) -> Fullname:
        _, module_name = self.fullname.pop_back()
        return module_name

    @property
    def extended_context(self) -> ExtendedContext:
        return ExtendedContext(context=self.context, path=self.file)
