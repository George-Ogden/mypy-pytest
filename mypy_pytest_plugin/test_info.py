from collections.abc import Iterable, Sequence
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

from .argnames_parser import ArgnamesParser
from .argvalues import Argvalues
from .decorator_wrapper import DecoratorWrapper
from .error_codes import (
    REPEATED_ARGNAME,
    UNKNOWN_ARGNAME,
)
from .fixture import Fixture
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .request import Request
from .request_graph import RequestGraph
from .test_argument import TestArgument
from .test_signature import TestSignature


@dataclass(frozen=True, kw_only=True)
class TestInfo:
    fullname: Fullname
    fn_name: str
    arguments: Sequence[TestArgument]
    decorators: Sequence[DecoratorWrapper]
    checker: TypeChecker

    @classmethod
    def from_fn_def(cls, fn_def: FuncDef | Decorator, *, checker: TypeChecker) -> Self | None:
        fn_def, decorators = cls._get_fn_and_decorators(fn_def)
        test_arguments = TestArgument.from_fn_def(fn_def, checker=checker)
        if test_arguments is None:
            return None
        test_decorators = DecoratorWrapper.decorators_from_nodes(decorators, checker=checker)
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
            arg_type=self._available_requests[arg_name].type_,
            type_variables=self._available_requests[arg_name].type_variables,
        )

    def many_items_sub_signature(self, arg_names: list[str]) -> TestSignature:
        return ManyItemsTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_names=arg_names,
            arg_types=[self._available_requests[arg_name].type_ for arg_name in arg_names],
            type_variables=list(
                itertools.chain.from_iterable(
                    self._available_requests[arg_name].type_variables for arg_name in arg_names
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
        available_requests, available_fixtures = self.fixture_manager.resolve_requests_and_fixtures(
            self.arguments, self.module_name
        )
        return RequestGraph(
            available_fixtures={fixture.name: fixture for fixture in available_fixtures},
            available_requests=available_requests,
            options=self.checker.options,
            name=self.name,
            checker=self.checker,
        )

    @property
    def _available_requests(self) -> dict[str, Request]:
        return self.request_graph.available_requests

    @property
    def _available_fixtures(self) -> dict[str, Fixture]:
        return self.request_graph.available_fixtures

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
        self, arg_names_node: Expression, arg_values_node: Expression
    ) -> None:
        arg_names = self._argnames_parser.parse_names(arg_names_node)
        if arg_names is not None and self._check_arg_names(arg_names, context=arg_names_node):
            sub_signature = self.sub_signature(arg_names)
            if sub_signature is not None:
                arg_values = Argvalues(arg_values_node)
                arg_values.check_against(sub_signature)

    def _check_arg_names(self, arg_names: str | list[str], *, context: Context) -> bool:
        if isinstance(arg_names, str):
            arg_names = [arg_names]
        return all([self._check_arg_name(arg_name, context) for arg_name in arg_names])

    def _check_arg_name(self, arg_name: str, context: Context) -> bool:
        if known_name := arg_name in self._available_requests:
            self._check_repeated_arg_name(arg_name, context)
        else:
            self.checker.fail(
                f"Unknown argname {arg_name!r} used as test argument.",
                context=context,
                code=UNKNOWN_ARGNAME,
            )
        return known_name

    def _check_repeated_arg_name(self, arg_name: str, context: Context) -> None:
        if self._available_requests[arg_name].used:
            self.checker.fail(
                f"Repeated argname {arg_name!r} in multiple parametrizations.",
                context=context,
                code=REPEATED_ARGNAME,
            )
        else:
            self._available_requests[arg_name].used = True
