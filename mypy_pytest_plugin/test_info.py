from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Self, cast

from mypy.checker import TypeChecker
from mypy.nodes import (
    Context,
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
    REPEATED_FIXTURE_ARGNAME,
    UNKNOWN_ARGNAME,
)
from .fixture import Fixture
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .many_items_test_signature import ManyItemsTestSignature
from .one_item_test_signature import OneItemTestSignature
from .request import Request
from .test_argument import TestArgument
from .test_signature import TestSignature


@dataclass(frozen=True, slots=True, kw_only=True)
class TestInfo:
    fullname: Fullname
    fn_name: str
    arguments: Sequence[TestArgument]
    decorators: Sequence[DecoratorWrapper]
    type_variables: Sequence[TypeVarLikeType]
    checker: TypeChecker
    _available_requests: dict[str, Request] = field(
        default_factory=dict, init=True, repr=False, hash=False, compare=False
    )
    _available_fixtures: dict[str, Fixture] = field(
        default_factory=dict, init=True, repr=False, hash=False, compare=False
    )

    @property
    def dummy_context(self) -> Context:
        return Context(-1, -1)

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
            arg_type=self._available_requests[arg_name].type_,
            type_variables=self.type_variables,
        )

    def many_items_sub_signature(self, arg_names: list[str]) -> TestSignature:
        return ManyItemsTestSignature(
            checker=self.checker,
            fn_name=self.fn_name,
            arg_names=arg_names,
            arg_types=[self._available_requests[arg_name].type_ for arg_name in arg_names],
            type_variables=self.type_variables,
        )

    def check(self) -> None:
        self.setup_available_requests_and_fixtures()
        self.check_decorators(self.decorators)
        active_requests, active_fixtures = self._prune_active_nodes_and_fixtures()
        self._check_request_graph(active_requests, active_fixtures)

    @property
    def module_name(self) -> Fullname:
        _, module_name = self.fullname.pop_back()
        return module_name

    @property
    def fixture_manager(self) -> FixtureManager:
        return FixtureManager(self.checker)

    def setup_available_requests_and_fixtures(self) -> None:
        available_requests, available_fixtures = self.fixture_manager.resolve_requests_and_fixtures(
            self.arguments, self.module_name
        )
        assert not self._available_requests
        assert not self._available_fixtures
        self._available_requests.update(available_requests)
        self._available_fixtures.update(
            {fixture.fullname.back: fixture for fixture in available_fixtures}
        )

    def _prune_active_nodes_and_fixtures(self) -> tuple[dict[str, Request], dict[str, Fixture]]:
        queue = deque(
            request for request in self._available_requests.values() if request.source == "argument"
        )
        active_request_names = set()
        while queue:
            request = queue.pop()
            if request.name in active_request_names:
                continue
            active_request_names.add(request.name)
            if not request.used and request.name in self._available_fixtures:
                queue.extend(
                    self._available_requests[argument.name]
                    for argument in self._available_fixtures[request.name].arguments
                )
        return {name: self._available_requests[name] for name in active_request_names}, {
            name: self._available_fixtures[name]
            for name in active_request_names
            if name in self._available_fixtures and not self._available_requests[name].used
        }

    def _check_request_graph(
        self, active_requests: dict[str, Request], active_fixtures: dict[str, Fixture]
    ) -> None:
        self._check_used(active_requests, active_fixtures)
        self._check_unused(active_requests)

    def _check_used(
        self, active_requests: dict[str, Request], active_fixtures: dict[str, Fixture]
    ) -> None:
        for request in active_requests.values():
            if not request.used and request.name not in active_fixtures:
                self.checker.fail(
                    f"Argname {request.name!r} not included in parametrization.",
                    context=request.context,
                    code=MISSING_ARGNAME,
                )

    def _check_unused(self, active_requests: dict[str, Request]) -> None:
        for request in self._available_requests.values():
            if request.used and request.name not in active_requests:
                self.checker.fail(
                    f"Argname {request.name!r} is invalid as the fixture is already provided.",
                    context=self.dummy_context,
                    code=REPEATED_FIXTURE_ARGNAME,
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
