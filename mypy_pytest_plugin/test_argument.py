from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self

from mypy.checker import TypeChecker
from mypy.nodes import (
    ArgKind,
    Argument,
    Context,
    FuncDef,
)
from mypy.types import CallableType, Type, TypeVarLikeType

from .error_codes import (
    OPTIONAL_ARGUMENT,
    POSITIONAL_ONLY_ARGUMENT,
    VARIADIC_KEYWORD_ARGUMENT,
    VARIADIC_POSITIONAL_ARGUMENT,
)
from .error_info import ExtendedContext
from .logger import Logger


@dataclass(frozen=True, slots=True, kw_only=True)
class TestArgument:
    name: str
    type_: Type
    type_variables: Sequence[TypeVarLikeType]
    context: Context

    @classmethod
    def from_fn_def(cls, fn_def: FuncDef, *, checker: TypeChecker) -> Sequence[Self] | None:
        if not isinstance(fn_def.type, CallableType):
            return None
        return cls._validate_test_arguments(
            fn_def.arguments, fn_def.type.arg_types, fn_def.type.variables, checker
        )

    @classmethod
    def _validate_test_arguments(
        cls,
        arguments: Sequence[Argument],
        types: Sequence[Type],
        type_variables: Sequence[TypeVarLikeType],
        checker: TypeChecker,
    ) -> Sequence[Self] | None:
        test_arguments: Sequence[Self | None] = [
            cls._validate_test_argument(argument, type_, type_variables, checker)
            for argument, type_ in zip(arguments, types, strict=True)
        ]
        return [argument for argument in test_arguments if argument is not None]

    @classmethod
    def _validate_test_argument(
        cls,
        argument: Argument,
        type_: Type,
        type_variables: Sequence[TypeVarLikeType],
        checker: TypeChecker,
    ) -> Self | None:
        if argument.initializer is not None:
            message = f"`{argument.variable.name}` has a default value and is therefore ignored."
            code = OPTIONAL_ARGUMENT
        elif argument.pos_only:
            message = f"`{argument.variable.name}` must not be positional only."
            code = POSITIONAL_ONLY_ARGUMENT
        elif argument.kind == ArgKind.ARG_STAR:
            message = (
                f"`*{argument.variable.name}` is variadic positional and is therefore ignored."
            )
            code = VARIADIC_POSITIONAL_ARGUMENT
        elif argument.kind == ArgKind.ARG_STAR2:
            message = (
                f"`**{argument.variable.name}` is variadic keyword-only and is therefore ignored."
            )
            code = VARIADIC_KEYWORD_ARGUMENT
        else:
            return cls(
                name=argument.variable.name,
                type_=type_,
                context=argument,
                type_variables=type_variables,
            )
        Logger.error(message, context=ExtendedContext.from_context(argument, checker), code=code)
        return None
