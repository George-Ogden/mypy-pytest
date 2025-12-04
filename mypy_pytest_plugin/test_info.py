from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import functools
import itertools
from typing import Self

from mypy.checker import TypeChecker
from mypy.nodes import (
    Context,
    Decorator,
    Expression,
    FuncDef,
)
from mypy.types import AnyType, TypeOfAny

from .argnames_parser import ArgnamesParser
from .argvalues import Argvalues
from .checker_wrapper import CheckerWrapper
from .decorator_wrapper import DecoratorWrapper
from .error_codes import (
    DUPLICATE_ARGNAME,
    UNKNOWN_ARGNAME,
)
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .request_graph import RequestGraph
from .test_argument import TestArgument
from .test_signature import TestSignature


@dataclass(frozen=True, kw_only=True)
class TestInfo(CheckerWrapper):
    fullname: Fullname
    fn_name: str
    arguments: Sequence[TestArgument]
    decorators: Sequence[DecoratorWrapper]
    checker: TypeChecker

    @classmethod
    def from_fn_def(cls, fn_def: FuncDef | Decorator, *, checker: TypeChecker) -> Self | None:
        fn_def, decorators = cls._get_fn_and_decorators(fn_def)
        test_arguments = TestArgument.from_fn_def(fn_def, checker=checker, source="test")
        if test_arguments is None:
            return None
        test_decorators = DecoratorWrapper.decorators_from_exprs(decorators, checker=checker)
        return cls(
            fullname=Fullname.from_string(fn_def.fullname),
            fn_name=fn_def.name,
            checker=checker,
            arguments=test_arguments,
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

    def sub_signature(self, arg_names: str | list[str]) -> TestSignature:
        if isinstance(arg_names, str):
            return self.one_item_sub_signature(arg_names)
        return self.many_items_sub_signature(arg_names)

    def one_item_sub_signature(self, arg_name: str) -> TestSignature:
        return OneItemTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_name=arg_name,
            arg_type=self._argname_types[arg_name].type_,
            type_variables=self._argname_types[arg_name].type_variables,
        )

    def many_items_sub_signature(self, arg_names: list[str]) -> TestSignature:
        return ManyItemsTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_names=arg_names,
            arg_types=[self._argname_types[arg_name].type_ for arg_name in arg_names],
            type_variables=list(
                itertools.chain.from_iterable(
                    self._argname_types[arg_name].type_variables for arg_name in arg_names
                )
            ),
        )

    @property
    def name(self) -> str:
        return self.fullname.name

    @property
    def module_name(self) -> Fullname:
        return self.fullname.module_name

    @property
    def fixture_manager(self) -> FixtureManager:
        return FixtureManager(self.checker)

    @functools.cached_property
    def request_graph(self) -> RequestGraph:
        available_fixtures = self.fixture_manager.resolve_fixtures(
            request_names=[argument.name for argument in self.arguments],
            parametrize_names=self.parametrized_argnames,
            test_module=self.module_name,
        )
        return RequestGraph.build(
            test_arguments=self.arguments,
            available_fixtures=available_fixtures,
            parametrized_names=self.parametrized_argnames,
            autouse_names=self.autouse_names,
            fullname=self.fullname,
            checker=self.checker,
        )

    @property
    def autouse_names(self) -> Iterable[str]:
        return self.fixture_manager.autouse_fixture_names(self.module_name)

    @property
    def _argname_types(self) -> Mapping[str, TestArgument]:
        return {
            request.name: TestArgument(
                type_=AnyType(TypeOfAny.special_form),
                type_variables=(),
                context=request.context,
                name=request.name,
            )
            for request in self.request_graph.requests
            if request.source == "argument"
        }
        return self.request_graph._argname_types

    @property
    def parametrized_argnames(self) -> Sequence[str]:
        return list(
            itertools.chain.from_iterable(
                self._decorator_argnames(decorator) for decorator in self.decorators
            )
        )

    def _decorator_argnames(self, decorator: DecoratorWrapper) -> list[str]:
        if decorator.arg_names is not None:
            match self._argnames_parser.parse_names(decorator.arg_names):
                case str() as argname:
                    return [argname]
                case [*argnames]:
                    return argnames
        return []

    def check(self) -> None:
        self.check_decorators(self.decorators)
        self.request_graph.check()

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
        self, arg_names_expr: Expression, arg_values_expr: Expression
    ) -> None:
        arg_names = self._argnames_parser.parse_names(arg_names_expr)
        if arg_names is not None and self._check_arg_names(arg_names, context=arg_names_expr):
            sub_signature = self.sub_signature(arg_names)
            if sub_signature is not None:
                arg_values = Argvalues(arg_values_expr)
                arg_values.check_against(sub_signature)

    def _check_arg_names(self, arg_names: str | list[str], *, context: Context) -> bool:
        if isinstance(arg_names, str):
            arg_names = [arg_names]
        return all([self._check_arg_name(arg_name, context) for arg_name in arg_names])

    def _check_arg_name(self, arg_name: str, context: Context) -> bool:
        if known_name := arg_name in self._argname_types:
            self._check_repeated_arg_name(arg_name, context)
        else:
            self.fail(
                f"Unknown argname {arg_name!r} used as test argument.",
                context=context,
                code=UNKNOWN_ARGNAME,
            )
        return known_name

    def _check_repeated_arg_name(self, arg_name: str, context: Context) -> None:
        return
        if todo:  # fixme
            self.fail(
                f"Repeated argname {arg_name!r} in multiple parametrizations.",
                context=context,
                code=DUPLICATE_ARGNAME,
            )
