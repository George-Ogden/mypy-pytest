from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass
import enum
from typing import ClassVar, Final, Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import (
    GDEF,
    CallExpr,
    Context,
    Decorator,
    Expression,
    FuncDef,
    SymbolTableNode,
    Var,
)
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
    UnionType,
)

from .argmapper import ArgMapper
from .checker_wrapper import CheckerWrapper
from .defer import DeferralError, DeferralReason
from .error_codes import (
    DUPLICATE_FIXTURE,
    INVALID_FIXTURE_AUTOUSE,
    INVALID_FIXTURE_SCOPE,
    MARKED_FIXTURE,
    REQUEST_KEYWORD,
)
from .fullname import Fullname
from .test_argument import TestArgument
from .types_module import TYPES_MODULE
from .utils import strict_cast, strict_not_none

FixtureScope = enum.IntEnum(
    "FixtureScope", ["function", "class", "module", "package", "session", "unknown"]
)
DEFAULT_SCOPE: Final[FixtureScope] = FixtureScope.function


@dataclass(frozen=True, slots=True, kw_only=True)
class Fixture:
    AUTOUSE_NAME: ClassVar[str] = "__autouse__"
    fullname: Fullname
    file: str
    return_type: Type
    arguments: Sequence[TestArgument]
    scope: FixtureScope
    autouse: bool
    type_variables: Sequence[TypeVarLikeType]
    context: Context

    @classmethod
    def from_decorator(cls, decorator: Decorator, checker: TypeChecker) -> Fixture | None:
        return FixtureParser(checker).from_decorator(decorator)

    @classmethod
    def from_type(
        cls,
        type: CallableType,
        *,
        scope: FixtureScope,
        file: str,
        is_generator: bool,
        autouse: bool,
        fullname: str,
    ) -> Self:
        func = type.definition
        assert isinstance(func, FuncDef | None)
        if isinstance(func, FuncDef):
            arguments = strict_not_none(
                TestArgument.from_fn_def(func, checker=None, source="fixture")
            )
            context: Context = func
        else:
            arguments = TestArgument.from_type(type)
            context = Context()
        return cls(
            fullname=Fullname.from_string(fullname),
            file=file,
            return_type=FixtureParser.fixture_return_type(type.ret_type, is_generator=is_generator),
            arguments=arguments,
            scope=scope,
            autouse=autouse,
            context=context,
            type_variables=type.variables,
        )

    @classmethod
    def is_fixture_and_mark(cls, decorator: Decorator, *, checker: TypeChecker) -> bool:
        return FixtureParser(checker).is_fixture_and_mark(decorator)

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

    def as_fixture_type(self, *, decorator: Decorator, checker: TypeChecker) -> Type:
        assert decorator.func.type is not None
        if self.autouse:
            self.save_to_autouse(checker)
        return checker.named_generic_type(
            f"{TYPES_MODULE}.FixtureType",
            [
                LiteralType(self.scope, fallback=checker.named_type("builtins.object")),
                decorator.func.type,
                LiteralType(
                    decorator.func.is_generator, fallback=checker.named_type("builtins.object")
                ),
                LiteralType(decorator.fullname, fallback=checker.named_type("builtins.object")),
                LiteralType(self.autouse, fallback=checker.named_type("builtins.object")),
            ],
        )

    def save_to_autouse(self, checker: TypeChecker) -> None:
        if str(self.module_name) in checker.modules:
            node = checker.modules[str(self.module_name)].names.setdefault(
                self.AUTOUSE_NAME,
                SymbolTableNode(
                    GDEF,
                    Var(
                        self.AUTOUSE_NAME,
                        UnionType([]),
                    ),
                    implicit=True,
                    module_hidden=True,
                    plugin_generated=True,
                ),
            )
            literal_type = LiteralType(
                self.name,
                fallback=checker.named_type("builtins.str"),
            )
            assert isinstance(node.node, Var)
            assert isinstance(node.type, UnionType)
            if not any(
                strict_cast(LiteralType, item).value == literal_type.value
                for item in node.type.items
            ):
                node.type.items.append(literal_type)


@dataclass(frozen=True, slots=True)
class FixtureParser(CheckerWrapper):
    checker: TypeChecker

    def from_decorator(self, decorator: Decorator) -> Fixture | None:
        fixture_decorator = self.fixture_decorator(decorator.decorators)
        if (
            fixture_decorator is None
            or (type_ := self.analyze_type(decorator.func)) is None
            or self._contains_mark_decorators(decorator.decorators)
            or self.is_request_name(decorator)
        ):
            return None
        arguments = TestArgument.from_fn_def(decorator.func, checker=self.checker, source="fixture")
        if arguments is None:
            return None
        return Fixture(
            fullname=Fullname.from_string(decorator.fullname),
            file=self.checker.path,
            return_type=self.fixture_return_type(
                type_.ret_type, is_generator=decorator.func.is_generator
            ),
            arguments=arguments,
            scope=self._fixture_scope_from_decorator(fixture_decorator),
            autouse=self._fixture_autouse_from_decorator(fixture_decorator),
            context=decorator.func,
            type_variables=type_.variables,
        )

    def analyze_type(self, func: FuncDef) -> CallableType | None:
        if func.type is None:
            func.type = CallableType(
                arg_names=func.arg_names,
                arg_types=[AnyType(TypeOfAny.unannotated)] * len(func.arguments),
                arg_kinds=func.arg_kinds,
                ret_type=AnyType(TypeOfAny.unannotated),
                fallback=self.checker.named_type("builtins.function"),
                definition=func,
            )
        if isinstance(func.type, CallableType):
            return func.type
        return None

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

    def is_fixture_and_mark(self, decorator: Decorator) -> bool:
        return bool(
            self.fixture_decorators(decorator.decorators)
        ) and self._contains_mark_decorators(decorator.decorators)

    def _contains_mark_decorators(self, decorators: list[Expression]) -> bool:
        return any([self._is_mark(decorator) for decorator in decorators])

    def _is_mark(self, expression: Expression) -> bool:
        if is_mark := is_subtype(
            self.checker.lookup_type(expression), self.checker.named_type("pytest.MarkDecorator")
        ):
            self.fail(
                "Marks cannot be applied to fixtures.",
                context=expression,
                code=MARKED_FIXTURE,
            )
        return is_mark

    def fixture_decorator(self, decorators: Sequence[Expression]) -> Expression | None:
        fixture_decorators = self.fixture_decorators(decorators)
        if len(fixture_decorators) == 1:
            [fixture_decorator] = fixture_decorators
            return fixture_decorator
        for decorator in fixture_decorators[1:]:
            self._warn_extra_decorator(decorator)
        return None

    def fixture_decorators(self, decorators: Sequence[Expression]) -> list[Expression]:
        return [decorator for decorator in decorators if self._is_fixture_decorator(decorator)]

    def _warn_extra_decorator(self, decorator: Expression) -> None:
        self.fail(
            "Extra `pytest.fixture` decorator. Only one is allowed.",
            context=decorator,
            code=DUPLICATE_FIXTURE,
        )

    def _is_fixture_decorator(self, decorator: Expression) -> bool:
        decorator_type = self.checker.lookup_type_or_none(decorator)
        if decorator_type is None:
            raise DeferralError(DeferralReason.REQUIRED_WAIT)
        return self._is_fixture_type(decorator_type) or (
            isinstance(decorator_type, Overloaded)
            and any(self._is_fixture_type(overload.ret_type) for overload in decorator_type.items)
        )

    @classmethod
    def _is_fixture_type(cls, type_: Type) -> bool:
        return (
            isinstance(type_, Instance)
            and type_.type.fullname == "_pytest.fixtures.FixtureFunctionMarker"
        )

    def _fixture_scope_from_decorator(self, decorator: Expression) -> FixtureScope:
        if isinstance(decorator, CallExpr):
            return self._fixture_scope_from_call(decorator)
        return DEFAULT_SCOPE

    def _fixture_scope_from_call(self, call: CallExpr) -> FixtureScope:
        scope_expression = ArgMapper.named_arg(call, "scope")
        if scope_expression is None:
            return DEFAULT_SCOPE
        return self._fixture_scope_from_type(
            self.checker.lookup_type(scope_expression), context=scope_expression
        )

    def _fixture_scope_from_type(self, type_: Type, context: Context) -> FixtureScope:
        if isinstance(type_, LiteralType) and type_.value in FixtureScope._member_names_:
            return FixtureScope[cast(str, type_.value)]
        self.fail(
            "Invalid type for fixture scope.",
            context=context,
            code=INVALID_FIXTURE_SCOPE,
        )

        return FixtureScope.unknown

    def _fixture_autouse_from_decorator(self, decorator: Expression) -> bool:
        if isinstance(decorator, CallExpr):
            return self._fixture_autouse_from_call(decorator)
        return False

    def _fixture_autouse_from_call(self, call: CallExpr) -> bool:
        autouse_expression = ArgMapper.named_arg(call, "autouse")
        if autouse_expression is None:
            return False
        return self._fixture_autouse_from_type(
            self.checker.lookup_type(autouse_expression), context=autouse_expression
        )

    def _fixture_autouse_from_type(self, type_: Type, context: Context) -> bool:
        for value in [True, False]:
            if is_subtype(
                type_, LiteralType(value, fallback=self.checker.named_type("builtins.bool"))
            ):
                return value
        if isinstance(type_, LiteralType) and isinstance(type_.value, bool):
            return type_.value
        self.fail(
            """Invalid type for "autouse". This fixture will be not be applied automatically when type checking.""",
            context=context,
            code=INVALID_FIXTURE_AUTOUSE,
        )
        self.note(
            "Use `autouse=True` directly.",
            context=context,
            code=INVALID_FIXTURE_AUTOUSE,
        )
        return False

    def is_request_name(self, decorator: Decorator) -> bool:
        if is_request_name := decorator.name == "request":
            self.fail(
                """"request" is a reserved name in Pytest. Use another name for this fixture.""",
                context=decorator.func,
                code=REQUEST_KEYWORD,
            )
        return is_request_name
