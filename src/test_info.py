from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import (
    ArgKind,
    Argument,
    Decorator,
    Expression,
    FuncDef,
    ListExpr,
    StrExpr,
    TupleExpr,
)
from mypy.types import CallableType, Type

from .argvalues import Argvalues
from .decorator_wrapper import DecoratorWrapper
from .error_codes import (
    DUPLICATE_ARGNAME,
    INVALID_ARGNAME,
    MISSING_ARGNAME,
    POSITIONAL_ONLY_ARGUMENT,
    REPEATED_ARGNAME,
    UNKNOWN_ARGNAME,
    UNREADABLE_ARGNAME,
    UNREADABLE_ARGNAMES,
    VARIADIC_KEYWORD_ARGUMENT,
    VARIADIC_POSITIONAL_ARGUMENT,
)
from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .test_signature import TestSignature


@dataclass(frozen=True, slots=True, kw_only=True)
class TestArgument:
    name: str
    type_: Type
    initialized: bool
    context: Argument


@dataclass(frozen=True, slots=True, kw_only=True)
class TestInfo:
    fn_name: str
    arguments: Mapping[str, TestArgument]
    decorators: Sequence[DecoratorWrapper]
    checker: TypeChecker
    seen_arg_names: set[str] = field(default_factory=set)

    @classmethod
    def from_fn_def(cls, fn_def: FuncDef | Decorator, *, checker: TypeChecker) -> Self | None:
        fn_def, decorators = cls._get_fn_and_decorators(fn_def)
        assert isinstance(fn_def.type, CallableType)
        test_arguments = cls._validate_test_arguments(
            fn_def.arguments, fn_def.type.arg_types, checker=checker
        )
        if test_arguments is None:
            return None
        test_decorators = DecoratorWrapper.decorators_from_nodes(decorators, checker=checker)
        return cls(
            fn_name=fn_def.name,
            checker=checker,
            arguments={test_argument.name: test_argument for test_argument in test_arguments},
            decorators=test_decorators,
        )

    @classmethod
    def _get_fn_and_decorators(
        cls, fn_def: FuncDef | Decorator
    ) -> tuple[FuncDef, Sequence[Expression]]:
        match fn_def:
            case FuncDef():
                return fn_def, []
            case Decorator():
                return fn_def.func, fn_def.original_decorators
            case _:
                raise TypeError()

    @classmethod
    def _validate_test_arguments(
        cls, arguments: Sequence[Argument], types: Sequence[Type], *, checker: TypeChecker
    ) -> Sequence[TestArgument] | None:
        test_arguments: Sequence[TestArgument | None] = [
            cls._validate_test_argument(argument, type_, checker=checker)
            for argument, type_ in zip(arguments, types, strict=True)
        ]
        if any(argument is None for argument in test_arguments):
            return None
        return cast(list[TestArgument], test_arguments)

    @classmethod
    def _validate_test_argument(
        cls, argument: Argument, type_: Type, *, checker: TypeChecker
    ) -> TestArgument | None:
        if argument.pos_only:
            checker.fail(
                f"`{argument.variable.name}` must not be positional only.",
                context=argument,
                code=POSITIONAL_ONLY_ARGUMENT,
            )
            return None
        if argument.kind == ArgKind.ARG_STAR:
            checker.fail(
                f"`*{argument.variable.name}` must not be variadic positional.",
                context=argument,
                code=VARIADIC_POSITIONAL_ARGUMENT,
            )
            return None
        if argument.kind == ArgKind.ARG_STAR2:
            checker.fail(
                f"`**{argument.variable.name}` must not be variadic keyword-only.",
                context=argument,
                code=VARIADIC_KEYWORD_ARGUMENT,
            )
            return None
        return TestArgument(
            name=argument.variable.name,
            type_=type_,
            initialized=argument.initializer is not None,
            context=argument,
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
            self.checker.fail(
                f"Duplicated argname {argname!r}.", context=context, code=DUPLICATE_ARGNAME
            )

    def _parse_names(self, node: Expression) -> str | list[str] | None:
        match node:
            case StrExpr():
                argnames = self.parse_names_string(node)
            case ListExpr() | TupleExpr():
                argnames = self.parse_names_sequence(node)
            case _:
                self.checker.fail(
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
        self.checker.fail(f"Invalid identifier {name!r}.", context=context, code=INVALID_ARGNAME)
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
            self.checker.fail(
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

    def sub_signature(self, arg_names: str | list[str]) -> TestSignature:
        if isinstance(arg_names, str):
            return self.one_item_sub_signature(arg_names)
        return self.many_items_sub_signature(arg_names)

    def one_item_sub_signature(self, arg_name: str) -> TestSignature:
        return OneItemTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_name=arg_name,
            arg_type=self.arguments[arg_name].type_,
        )

    def many_items_sub_signature(self, arg_names: list[str]) -> TestSignature:
        return ManyItemsTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_names=arg_names,
            arg_types=[self.arguments[arg_name].type_ for arg_name in arg_names],
        )

    def check(self) -> None:
        self.check_decorators(reversed(self.decorators))
        self._check_missing_argnames()

    def _check_missing_argnames(self) -> None:
        missing_arg_names = set(self.arguments.keys()).difference(self.seen_arg_names)
        for arg_name in missing_arg_names:
            self.checker.fail(
                f"Argname {arg_name!r} not included in parametrization.",
                context=self.arguments[arg_name].context,
                code=MISSING_ARGNAME,
            )

    def check_decorators(self, decorators: Iterable[DecoratorWrapper]) -> None:
        for decorator in decorators:
            self.check_decorator(decorator)

    def check_decorator(self, decorator: DecoratorWrapper) -> None:
        arg_names_and_arg_values = decorator.arg_names_and_arg_values
        if arg_names_and_arg_values is not None:
            self._check_argnames_and_argvalues(*arg_names_and_arg_values)

    def _check_argnames_and_argvalues(
        self, arg_names_node: Expression, arg_values_node: Expression
    ) -> None:
        arg_names = self._parse_names(arg_names_node)
        if arg_names is not None and self._check_arg_names(arg_names, context=arg_names_node):
            sub_signature = self.sub_signature(arg_names)
            if sub_signature is not None:
                arg_values = Argvalues(arg_values_node)
                arg_values.check_against(sub_signature)

    def _check_arg_names(self, arg_names: str | list[str], *, context: Expression) -> bool:
        if isinstance(arg_names, str):
            arg_names = [arg_names]
        return all([self._check_arg_name(arg_name, context) for arg_name in arg_names])

    def _check_arg_name(self, arg_name: str, context: Expression) -> bool:
        if arg_name in self.arguments:
            self._check_repeated_arg_name(arg_name, context)
            return True
        self.checker.fail(
            f"Unknown argname {arg_name!r} used as test argument.",
            context=context,
            code=UNKNOWN_ARGNAME,
        )
        return False

    def _check_repeated_arg_name(self, arg_name: str, context: Expression) -> None:
        if arg_name in self.seen_arg_names:
            self.checker.fail(
                f"Repeated argname {arg_name!r} in multiple parametrizations.",
                context=context,
                code=REPEATED_ARGNAME,
            )
        else:
            self.seen_arg_names.add(arg_name)
