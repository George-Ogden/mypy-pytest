from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import ArgKind, Argument, Expression, FuncDef, ListExpr, StrExpr, TupleExpr
from mypy.types import AnyType, Type, TypeOfAny

from .error_codes import (
    DUPLICATE_ARGNAME,
    INVALID_ARGNAME,
    POSITIONAL_ONLY_ARGUMENT,
    UNREADABLE_ARGNAME,
    UNREADABLE_ARGNAMES,
    VARIADIC_KEYWORD_ARGUMENT,
    VARIADIC_POSITIONAL_ARGUMENT,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class TestArgument:
    name: str
    type_: Type
    initialized: bool


@dataclass(frozen=True, slots=True, kw_only=True)
class TestInfo:
    fn_name: str
    arguments: Sequence[TestArgument]
    checker: TypeChecker

    @classmethod
    def from_fn_def(cls, fn_def: FuncDef, *, checker: TypeChecker) -> Self | None:
        test_arguments = cls._validate_test_arguments(fn_def.arguments, checker=checker)
        if test_arguments is None:
            return None
        return cls(checker=checker, fn_name=fn_def.name, arguments=test_arguments)

    @classmethod
    def _validate_test_arguments(
        cls, arguments: Sequence[Argument], *, checker: TypeChecker
    ) -> Sequence[TestArgument] | None:
        test_arguments: Sequence[TestArgument | None] = [
            cls._validate_test_argument(argument, checker=checker) for argument in arguments
        ]
        if any(argument is None for argument in test_arguments):
            return None
        return cast(list[TestArgument], test_arguments)

    @classmethod
    def _validate_test_argument(
        cls, argument: Argument, *, checker: TypeChecker
    ) -> TestArgument | None:
        if argument.pos_only:
            checker.msg.fail(
                f"`{argument.variable.name}` must not be positional only.",
                context=argument,
                code=POSITIONAL_ONLY_ARGUMENT,
            )
            return None
        if argument.kind == ArgKind.ARG_STAR:
            checker.msg.fail(
                f"`*{argument.variable.name}` must not be variadic positional.",
                context=argument,
                code=VARIADIC_POSITIONAL_ARGUMENT,
            )
            return None
        if argument.kind == ArgKind.ARG_STAR2:
            checker.msg.fail(
                f"`**{argument.variable.name}` must not be variadic keyword-only.",
                context=argument,
                code=VARIADIC_KEYWORD_ARGUMENT,
            )
            return None
        return TestArgument(
            name=argument.variable.name,
            type_=argument.type_annotation
            or AnyType(TypeOfAny.unannotated, line=argument.line, column=argument.column),
            initialized=argument.initializer is not None,
        )

    def _check_duplicate_argnames(
        self, argnames: str | list[str] | None, context: Expression
    ) -> str | list[str] | None:
        if isinstance(argnames, list):
            return self._check_duplicate_argnames_sequence(argnames, context)
        return argnames

    def _check_duplicate_argnames_sequence(
        self, argnames: list[str], context: Expression
    ) -> None | list[str]:
        argname_counts = Counter(argnames)
        duplicates = [argname for argname, count in argname_counts.items() if count > 1]
        if duplicates:
            self._warn_duplicate_argnames(duplicates, context)
            return None
        return argnames

    def _warn_duplicate_argnames(self, duplicates: Iterable[str], context: Expression) -> None:
        for argname in duplicates:
            self.checker.msg.fail(
                f"Duplicated argname {argname!r}.", context=context, code=DUPLICATE_ARGNAME
            )

    def _parse_names(self, node: Expression) -> str | list[str] | None:
        match node:
            case StrExpr():
                argnames = self.parse_names_string(node)
            case ListExpr() | TupleExpr():
                argnames = self.parse_names_sequence(node)
            case _:
                self.checker.msg.fail(
                    "Unable to identify argnames. (Use a comma-separated string, list of strings or tuple of strings).",
                    context=node,
                    code=UNREADABLE_ARGNAMES,
                )
                return None
        argnames = self._check_duplicate_argnames(argnames, node)
        return argnames

    def _check_valid_identifier(self, name: str, context: StrExpr) -> bool:
        if name.isidentifier():
            return True
        self.checker.msg.fail(
            f"Invalid identifier {name!r}.", context=context, code=INVALID_ARGNAME
        )
        return False

    def parse_names_string(self, node: StrExpr) -> str | list[str] | None:
        individual_names = [name.strip() for name in node.value.split(",")]
        filtered_names = [name for name in individual_names if name]
        if any([not self._check_valid_identifier(name, node) for name in filtered_names]):
            return None
        if len(filtered_names) == 1:
            [name] = filtered_names
            return name
        return filtered_names

    def _parse_name(self, node: Expression) -> str | None:
        if isinstance(node, StrExpr):
            name = node.value
            if self._check_valid_identifier(name, node):
                return name
        else:
            self.checker.msg.fail(
                "Unable to read identifier. (Use a sequence of strings instead.)",
                context=node,
                code=UNREADABLE_ARGNAME,
            )
        return None

    def parse_names_sequence(self, node: TupleExpr | ListExpr) -> list[str] | None:
        names = [self._parse_name(item) for item in node.items]
        if all([isinstance(name, str) for name in names]):
            return cast(list[str], names)
        return None
