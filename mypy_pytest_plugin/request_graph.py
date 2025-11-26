from collections import deque
from dataclasses import dataclass
import functools

from mypy.checker import TypeChecker
from mypy.messages import format_type
from mypy.nodes import (
    Context,
)
from mypy.options import Options
from mypy.subtypes import is_subtype
from mypy.types import Type

from .error_codes import (
    FIXTURE_ARGUMENT_TYPE,
    INVERTED_FIXTURE_SCOPE,
    MISSING_ARGNAME,
    REPEATED_FIXTURE_ARGNAME,
)
from .fixture import Fixture, FixtureScope
from .request import Request


@dataclass(frozen=True, kw_only=True)
class RequestGraph:
    name: str
    checker: TypeChecker
    available_requests: dict[str, Request]
    available_fixtures: dict[str, Fixture]
    options: Options

    @functools.cached_property
    def dummy_context(self) -> Context:
        earliest_context = min(
            (
                request.request.context
                for request in self.available_requests.values()
                if request.source == "argument"
            ),
            key=lambda context: (context.line, context.column),
        )
        if earliest_context:
            context = Context(earliest_context.line, max(earliest_context.column - 1, 0))
            context.end_line = context.line
            context.end_column = context.column
            return context
        return Context(-1, -1)

    def check(self) -> None:
        active_requests, active_fixtures = self._prune_active_nodes_and_fixtures()
        self._check_request_graph(active_requests, active_fixtures)

    def _prune_active_nodes_and_fixtures(self) -> tuple[dict[str, Request], dict[str, Fixture]]:
        queue = deque(
            request for request in self.available_requests.values() if request.source == "argument"
        )
        active_requests: dict[str, Request] = {}
        active_fixtures = {}
        while queue:
            request = queue.pop()
            if request.name in active_requests.keys():
                continue
            active_requests[request.name] = request
            if not request.used and request.name in self.available_fixtures:
                active_fixtures[request.name] = self.available_fixtures[request.name]
                queue.extend(
                    self.available_requests[argument.name]
                    for argument in self.available_fixtures[request.name].arguments
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
                self.checker.msg.fail(
                    f"Argname {request.name!r} not included in parametrization.",
                    context=request.context if request.source == "argument" else self.dummy_context,
                    file=request.file,
                    code=MISSING_ARGNAME,
                )

    def _check_unused(self, active_requests: dict[str, Request]) -> None:
        for request in self.available_requests.values():
            if request.used and request.name not in active_requests:
                self.checker.fail(
                    f"Argname {request.name!r} is invalid as the fixture is shadowed by another argument.",
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
                    self.checker.msg.fail(
                        f"{fixture.name!r} (scope={fixture.scope.name!r}) requests {requested_fixture.name!r} (scope={requested_fixture.scope.name!r}).",
                        context=fixture.context,
                        file=fixture.file,
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
                self.checker.msg.fail(
                    f"{fixture.name!r} requests {argument.name!r} with type {format_type(requested_types[argument.name], self.options)}, but expects type {format_type(argument.type_, self.options)}. "
                    f"This happens when executing {self.name!r}.",
                    context=fixture.context,
                    file=fixture.file,
                    code=FIXTURE_ARGUMENT_TYPE,
                )

    def _check_argument_types(self, active_fixtures: dict[str, Fixture]) -> None:
        for request in self.available_requests.values():
            if (
                request.source == "argument"
                and request.name in active_fixtures.keys()
                and not is_subtype(
                    received_type := active_fixtures[request.name].return_type, request.type_
                )
            ):
                self.checker.msg.fail(
                    f"{self.name!r} requests {request.name!r} with type {format_type(received_type, self.options)}, but expects type {format_type(request.request.type_, self.options)}.",
                    context=request.context,
                    file=request.file,
                    code=FIXTURE_ARGUMENT_TYPE,
                )
