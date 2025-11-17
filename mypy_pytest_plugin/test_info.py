from collections import deque
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
import itertools
from typing import Self

from mypy.checker import TypeChecker
from mypy.messages import format_type
from mypy.nodes import (
    Context,
    Decorator,
    Expression,
    FuncDef,
)
from mypy.subtypes import is_subtype
from mypy.types import Type

from .argnames_parser import ArgnamesParser
from .argvalues import Argvalues
from .decorator_wrapper import DecoratorWrapper
from .error_codes import (
    FIXTURE_ARGUMENT_TYPE,
    INVERTED_FIXTURE_SCOPE,
    MISSING_ARGNAME,
    REPEATED_ARGNAME,
    REPEATED_FIXTURE_ARGNAME,
    UNKNOWN_ARGNAME,
)
from .error_info import ExtendedContext
from .fixture import Fixture, FixtureScope
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .logger import Logger
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
    checker: TypeChecker
    _available_requests: dict[str, Request] = field(
        default_factory=dict, init=True, repr=False, hash=False, compare=False
    )
    _available_fixtures: dict[str, Fixture] = field(
        default_factory=dict, init=True, repr=False, hash=False, compare=False
    )

    @property
    def dummy_context(self) -> ExtendedContext:
        return ExtendedContext(
            context=Context(-1, -1), path=ExtendedContext.checker_path(self.checker)
        )

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

    def check(self) -> None:
        self.setup_available_requests_and_fixtures()
        self.check_decorators(self.decorators)
        active_requests, active_fixtures = self._prune_active_nodes_and_fixtures()
        self._check_request_graph(active_requests, active_fixtures)

    @property
    def name(self) -> str:
        return self.fullname.back

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
        self._available_fixtures.update({fixture.name: fixture for fixture in available_fixtures})

    def _prune_active_nodes_and_fixtures(self) -> tuple[dict[str, Request], dict[str, Fixture]]:
        queue = deque(
            request for request in self._available_requests.values() if request.source == "argument"
        )
        active_requests: dict[str, Request] = {}
        active_fixtures = {}
        while queue:
            request = queue.pop()
            if request.name in active_requests.keys():
                continue
            active_requests[request.name] = request
            if not request.used and request.name in self._available_fixtures:
                active_fixtures[request.name] = self._available_fixtures[request.name]
                queue.extend(
                    self._available_requests[argument.name]
                    for argument in self._available_fixtures[request.name].arguments
                )
        return active_requests, active_fixtures

    def _check_request_graph(
        self, active_requests: dict[str, Request], active_fixtures: dict[str, Fixture]
    ) -> None:
        self._check_used(active_requests, active_fixtures)
        self._check_unused(active_requests)
        self._check_scope(active_fixtures)
        self._check_fixture_types(active_fixtures)
        self._check_argument_types(active_fixtures)

    def _check_used(
        self, active_requests: dict[str, Request], active_fixtures: dict[str, Fixture]
    ) -> None:
        for request in active_requests.values():
            if not request.used and request.name not in active_fixtures:
                Logger.error(
                    f"Argname {request.name!r} not included in parametrization.",
                    context=request.context,
                    code=MISSING_ARGNAME,
                )

    def _check_unused(self, active_requests: dict[str, Request]) -> None:
        for request in self._available_requests.values():
            if request.used and request.name not in active_requests:
                Logger.error(
                    f"Argname {request.name!r} is invalid as the fixture is already provided.",
                    context=self.dummy_context,
                    code=REPEATED_FIXTURE_ARGNAME,
                )

    def _check_scope(self, active_fixtures: dict[str, Fixture]) -> None:
        for fixture in active_fixtures.values():
            for argument in fixture.arguments:
                requested_fixture = active_fixtures.get(argument.name)
                if (
                    requested_fixture is not None
                    and requested_fixture.scope < fixture.scope
                    and FixtureScope.unknown
                    not in [
                        requested_fixture.scope,
                        fixture.scope,
                    ]
                ):
                    Logger.error(
                        f"{fixture.name!r} (scope={fixture.scope.name!r}) requests {requested_fixture.name!r} (scope={requested_fixture.scope.name!r}).",
                        context=fixture.extended_context,
                        code=INVERTED_FIXTURE_SCOPE,
                    )

    def _check_fixture_types(self, active_fixtures: dict[str, Fixture]) -> None:
        for fixture in active_fixtures.values():
            requested_types = {
                argument.name: active_fixtures[argument.name].return_type
                for argument in fixture.arguments
                if argument.name in active_fixtures
            }
            self._check_fixture_call(fixture, requested_types)

    def _check_fixture_call(self, fixture: Fixture, requested_types: dict[str, Type]) -> None:
        for argument in fixture.arguments:
            if argument.name in requested_types.keys() and not is_subtype(
                requested_types[argument.name], argument.type_
            ):
                Logger.error(
                    f"{fixture.name!r} requests {argument.name!r} with type {format_type(requested_types[argument.name], self.checker.options)}, but expects type {format_type(argument.type_, self.checker.options)}. "
                    f"This happens when executing {self.name!r}.",
                    context=fixture.extended_context,
                    code=FIXTURE_ARGUMENT_TYPE,
                )

    def _check_argument_types(self, active_fixtures: dict[str, Fixture]) -> None:
        for request in self._available_requests.values():
            if (
                request.source == "argument"
                and request.name in active_fixtures.keys()
                and not is_subtype(
                    received_type := active_fixtures[request.name].return_type, request.type_
                )
            ):
                Logger.error(
                    f"{self.name!r} requests {request.name!r} with type {format_type(received_type, self.checker.options)}, but expects type {format_type(request.request.type_, self.checker.options)}.",
                    context=request.context,
                    code=FIXTURE_ARGUMENT_TYPE,
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
            Logger.error(
                f"Unknown argname {arg_name!r} used as test argument.",
                context=ExtendedContext.from_context(context, self.checker),
                code=UNKNOWN_ARGNAME,
            )
        return known_name

    def _check_repeated_arg_name(self, arg_name: str, context: Context) -> None:
        if self._available_requests[arg_name].used:
            Logger.error(
                f"Repeated argname {arg_name!r} in multiple parametrizations.",
                context=ExtendedContext.from_context(context, self.checker),
                code=REPEATED_ARGNAME,
            )
        else:
            self._available_requests[arg_name].used = True
