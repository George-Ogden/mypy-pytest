from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import (
    Decorator,
    Expression,
    FuncDef,
)
from mypy.types import CallableType, TypeVarLikeType

from .argnames_parser import ArgnamesParser
from .argvalues import Argvalues
from .decorator_wrapper import DecoratorWrapper
from .error_codes import (
    MISSING_ARGNAME,
    REPEATED_ARGNAME,
    UNKNOWN_ARGNAME,
)
from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .test_argument import TestArgument
from .test_signature import TestSignature


@dataclass(frozen=True, slots=True, kw_only=True)
class TestInfo:
    fn_name: str
    arguments: Mapping[str, TestArgument]
    decorators: Sequence[DecoratorWrapper]
    type_variables: Sequence[TypeVarLikeType]
    checker: TypeChecker
    seen_arg_names: set[str] = field(default_factory=set)

    @classmethod
    def from_fn_def(cls, fn_def: FuncDef | Decorator, *, checker: TypeChecker) -> Self | None:
        fn_def, decorators = cls._get_fn_and_decorators(fn_def)
        test_arguments = TestArgument.from_fn_def(fn_def, checker=checker)
        if test_arguments is None:
            return None
        test_decorators = DecoratorWrapper.decorators_from_nodes(decorators, checker=checker)
        return cls(
            fn_name=fn_def.name,
            checker=checker,
            arguments={test_argument.name: test_argument for test_argument in test_arguments},
            decorators=test_decorators,
            type_variables=cast(CallableType, fn_def.type).variables,
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
            type_variables=self.type_variables,
        )

    def many_items_sub_signature(self, arg_names: list[str]) -> TestSignature:
        return ManyItemsTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_names=arg_names,
            arg_types=[self.arguments[arg_name].type_ for arg_name in arg_names],
            type_variables=self.type_variables,
        )

    def check(self) -> None:
        self.check_decorators(self.decorators)
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

    @property
    def _argnames_parser(self) -> ArgnamesParser:
        return ArgnamesParser(self.checker)

    def _check_argnames_and_argvalues(
        self, arg_names_node: Expression, arg_values_node: Expression
    ) -> None:
        arg_names = self._argnames_parser.parse_names(arg_names_node)
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
        if known_name := arg_name in self.arguments:
            self._check_repeated_arg_name(arg_name, context)
        else:
            self.checker.fail(
                f"Unknown argname {arg_name!r} used as test argument.",
                context=context,
                code=UNKNOWN_ARGNAME,
            )
        return known_name

    def _check_repeated_arg_name(self, arg_name: str, context: Expression) -> None:
        if arg_name in self.seen_arg_names:
            self.checker.fail(
                f"Repeated argname {arg_name!r} in multiple parametrizations.",
                context=context,
                code=REPEATED_ARGNAME,
            )
        else:
            self.seen_arg_names.add(arg_name)
