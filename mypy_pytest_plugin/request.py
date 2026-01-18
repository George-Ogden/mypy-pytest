from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import itertools
from typing import Literal, Self

from mypy.checker import TypeChecker
from mypy.errorcodes import ErrorCode
from mypy.messages import format_type
from mypy.nodes import (
    ArgKind,
    Argument,
    Context,
    FuncDef,
    TypeInfo,
)
from mypy.subtypes import is_subtype
from mypy.types import (
    AnyType,
    CallableType,
    FormalArgument,
    Instance,
    Type,
    TypeOfAny,
    TypeVarLikeType,
)

from .error_codes import (
    OPTIONAL_ARGUMENT,
    POSITIONAL_ONLY_ARGUMENT,
    REQUEST_TYPE,
    VARIADIC_KEYWORD_ARGUMENT,
    VARIADIC_POSITIONAL_ARGUMENT,
)
from .utils import filter_unique


@dataclass(frozen=True, slots=True, kw_only=True)
class Request:
    name: str
    type_: Type
    type_variables: Sequence[TypeVarLikeType]
    context: Context

    @classmethod
    def from_fn_def(
        cls, fn_def: FuncDef, *, checker: TypeChecker | None, source: Literal["test", "fixture"]
    ) -> Sequence[Request] | None:
        return RequestParser(checker).parse_fn_def(fn_def, source=source)

    @classmethod
    def from_type(cls, type: CallableType) -> Sequence[Request]:
        return [
            argument
            for formal_argument in type.formal_arguments()
            if (
                argument := Request.from_formal_argument(
                    formal_argument, type_variables=type.variables
                )
            )
            is not None
        ]

    @classmethod
    def from_formal_argument(
        cls, argument: FormalArgument, type_variables: Sequence[TypeVarLikeType]
    ) -> Self | None:
        if argument.name is None or argument.name == "request":
            return None
        return cls(
            name=argument.name, type_=argument.typ, type_variables=type_variables, context=Context()
        )

    @classmethod
    def extend(
        cls, requests: Sequence[Request], extra_requests: Iterable[Request]
    ) -> Sequence[Request]:
        return list(
            filter_unique(
                itertools.chain(requests, extra_requests), key=lambda request: request.name
            )
        )


@dataclass(frozen=True, slots=True)
class RequestParser:
    checker: TypeChecker | None

    def parse_fn_def(
        self, fn_def: FuncDef, *, source: Literal["test", "fixture"]
    ) -> Sequence[Request] | None:
        if not isinstance(fn_def.type, CallableType):
            return None
        return self.filter_request_arguments(
            self._validate_test_arguments(
                fn_def.arguments, fn_def.type.arg_types, fn_def.type.variables
            ),
            source=source,
        )

    def _validate_test_arguments(
        self,
        arguments: Sequence[Argument],
        types: Sequence[Type],
        type_variables: Sequence[TypeVarLikeType],
    ) -> Sequence[Request]:
        requests: Sequence[Request | None] = [
            self._validate_test_argument(argument, type_, type_variables)
            for argument, type_ in zip(arguments, types, strict=True)
        ]
        return [argument for argument in requests if argument is not None]

    def _validate_test_argument(
        self,
        argument: Argument,
        type_: Type,
        type_variables: Sequence[TypeVarLikeType],
    ) -> Request | None:
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
            return Request(
                name=argument.variable.name,
                type_=type_,
                context=argument,
                type_variables=type_variables,
            )
        self.fail(message, context=argument, code=code)
        return None

    def filter_request_arguments(
        self,
        arguments: Sequence[Request] | None,
        *,
        source: Literal["test", "fixture"],
    ) -> Sequence[Request] | None:
        if arguments is None:
            return None
        match source:
            case "test":
                expected_type = self._fixture_type("TopRequest")
            case "fixture":
                expected_type = self._fixture_type("SubRequest")
            case _:
                raise TypeError()
        return self._filter_request_argument(arguments, expected_type)

    def _fixture_type(self, type_name: str) -> Type | None:
        if self.checker is None:
            return None
        module = self.checker.modules["_pytest.fixtures"]
        type_info = module.names[type_name].node
        assert isinstance(type_info, TypeInfo)
        return Instance(
            type_info, [AnyType(TypeOfAny.from_omitted_generics)] * len(type_info.defn.type_vars)
        )

    def _filter_request_argument(
        self, arguments: Sequence[Request], expected_type: Type | None
    ) -> Sequence[Request]:
        return [
            argument
            for argument in arguments
            if not self._is_request_argument(argument, expected_type)
        ]

    def _is_request_argument(self, argument: Request, expected_type: Type | None) -> bool:
        if (
            (is_request := (argument.name == "request"))
            and expected_type is not None
            and not is_subtype(expected_type, argument.type_)
        ):
            assert self.checker is not None
            self.fail(
                f""""request" passed to test should have type {format_type(expected_type, self.checker.options)}, but has type {format_type(argument.type_, self.checker.options)}.""",
                context=argument.context,
                code=REQUEST_TYPE,
            )
        return is_request

    def fail(self, message: str, context: Context, code: ErrorCode) -> None:
        if self.checker is not None:
            self.checker.fail(message, context=context, code=code)
