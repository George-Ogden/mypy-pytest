from collections.abc import Collection, Sequence
from dataclasses import dataclass
import enum
from typing import ClassVar, Final, Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Context, Decorator, Expression, FuncDef
from mypy.subtypes import is_subtype
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    LiteralType,
    Overloaded,
    Type,
    TypeOfAny,
    TypeVarLikeType,
)

from .defer import DeferralError
from .error_codes import DUPLICATE_FIXTURE, INVALID_FIXTURE_SCOPE, MARKED_FIXTURE
from .fullname import Fullname
from .test_argument import TestArgument

FixtureScope = enum.IntEnum(
    "FixtureScope", ["function", "class", "module", "package", "session", "unknown"]
)
DEFAULT_SCOPE: Final[FixtureScope] = FixtureScope.function


@dataclass(frozen=True, slots=True, kw_only=True)
class Fixture:
    fullname: Fullname
    file: str
    return_type: Type
    arguments: Sequence[TestArgument]
    scope: FixtureScope
    type_variables: Sequence[TypeVarLikeType]
    context: FuncDef

    @classmethod
    def from_decorator(cls, decorator: Decorator, checker: TypeChecker) -> Self | None:
        fixture_decorator = cls.fixture_decorator(decorator.decorators, checker)
        if (
            fixture_decorator is None
            or not isinstance(type_ := decorator.func.type, CallableType)
            or cls._contains_mark_decorators(decorator.decorators, checker)
        ):
            return None
        arguments = TestArgument.from_fn_def(decorator.func, checker=checker, source="fixture")
        if arguments is None:
            return None
        return cls(
            fullname=Fullname.from_string(decorator.fullname),
            file=checker.path,
            return_type=cls.fixture_return_type(
                type_.ret_type, is_generator=decorator.func.is_generator
            ),
            arguments=arguments,
            scope=cls._fixture_scope_from_decorator(fixture_decorator, checker),
            context=decorator.func,
            type_variables=type_.variables,
        )

    @classmethod
    def from_type(cls, type: CallableType, *, scope: FixtureScope, file: str) -> Self:
        func = type.definition
        assert isinstance(func, FuncDef)
        assert isinstance(func.type, CallableType)
        arguments = TestArgument.from_fn_def(func, checker=None, source="fixture")
        assert arguments is not None
        return cls(
            fullname=Fullname.from_string(func.fullname),
            file=file,
            return_type=cls.fixture_return_type(func.type.ret_type, is_generator=func.is_generator),
            arguments=arguments,
            scope=scope,
            context=func,
            type_variables=func.type.variables,
        )

    GENERATOR_TYPE_NAMES: ClassVar[Collection[str]] = (
        "typing.Generator",
        "typing.Iterable",
        "typing.Iterator",
    )

    @classmethod
    def fixture_return_type(cls, original_type: Type, *, is_generator: bool) -> Type:
        if is_generator:
            if (
                isinstance(original_type, Instance)
                and original_type.type.fullname in cls.GENERATOR_TYPE_NAMES
            ):
                return original_type.args[0]
            return AnyType(TypeOfAny.from_error)
        return original_type

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
            checker.fail(
                "Marks cannot be applied to fixtures.",
                context=expression,
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
        checker.fail(
            "Extra `pytest.fixture` decorator. Only one is allowed.",
            context=decorator,
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
        checker.fail(
            "Invalid type for fixture scope.",
            context=context,
            code=INVALID_FIXTURE_SCOPE,
        )

        return FixtureScope.unknown

    def as_argument(self) -> TestArgument:
        return TestArgument(
            name=self.name,
            type_=self.return_type,
            context=self.context,
            type_variables=self.type_variables,
        )

    @property
    def name(self) -> str:
        return self.fullname.name

    @property
    def module_name(self) -> Fullname:
        return self.fullname.module_name
