from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import functools
from typing import Any, TypeGuard, cast

from mypy.checker import TypeChecker
from mypy.messages import format_type
from mypy.nodes import Context, FuncDef
from mypy.options import Options
from mypy.subtypes import is_subtype
from mypy.types import CallableType

from .checker_wrapper import CheckerWrapper
from .error_codes import (
    FIXTURE_ARGUMENT_TYPE,
    INVERTED_FIXTURE_SCOPE,
    MISSING_ARGNAME,
)
from .fixture import Fixture, FixtureScope
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .request import Request
from .test_argument import TestArgument


@dataclass(frozen=True, slots=True, eq=False)
class RequestGraphBuilder:
    original_requests: Sequence[Request]
    available_fixtures: Mapping[str, Sequence[Fixture]]
    parametrized_names: Collection[str]
    requests: list[Request] = field(default_factory=list, init=False)
    visited_fixture_ids: set[int] = field(default_factory=set, init=False)

    def build(self) -> None:
        for request in self.original_requests:
            self.resolve_request(request, [request.name])

    def resolve_request(self, request: Request, path: list[str]) -> None:
        self.requests.append(request)
        if request.name in self.parametrized_names:
            request.resolver = "param"
        else:
            idx = path.count(request.name) - 1
            if idx < len(self.available_fixtures[request.name]):
                fixture = self.available_fixtures[request.name][idx]
                request.resolver = fixture
                if id(fixture) not in self.visited_fixture_ids:
                    self.visited_fixture_ids.add(id(fixture))
                    for arg in fixture.arguments:
                        request = Request(
                            arg,
                            file=fixture.file,
                            source="fixture",
                            scope=fixture.scope,
                            source_name=request.name,
                        )
                        path.append(arg.name)
                        self.resolve_request(request, path)
                        path.pop()


@dataclass(frozen=True, kw_only=True)
class RequestGraph(CheckerWrapper):
    fullname: Fullname
    checker: TypeChecker
    requests: Sequence[Request]

    @classmethod
    def build(
        cls,
        *,
        test_arguments: Iterable[TestArgument],
        autouse_names: Iterable[str],
        parametrized_names: Collection[str],
        available_fixtures: Mapping[str, Sequence[Fixture]],
        fullname: Fullname,
        checker: TypeChecker,
    ) -> RequestGraph:
        original_requests = [
            Request(test_arg, file=checker.path, source="argument", source_name=fullname.name)
            for test_arg in test_arguments
        ]
        original_requests.extend(
            Request.from_autouse_name(autouse_name, module=fullname.module_name, checker=checker)
            for autouse_name in autouse_names
        )
        builder = RequestGraphBuilder(
            original_requests=original_requests,
            available_fixtures=available_fixtures,
            parametrized_names=parametrized_names,
        )

        builder.build()
        return cls(fullname=fullname, checker=checker, requests=builder.requests)

    @property
    def name(self) -> str:
        return self.fullname.name

    @property
    def module_name(self) -> Fullname:
        return self.fullname.module_name

    @property
    def options(self) -> Options:
        return self.checker.options

    @functools.cached_property
    def dummy_context(self) -> Context:
        earliest_context = min(
            (request.request.context for request in self.requests if request.source == "argument"),
            key=lambda context: (context.line, context.column),
        )
        if earliest_context:
            context = Context(earliest_context.line, max(earliest_context.column - 1, 0))
            context.end_line = context.line
            context.end_column = context.column
            return context
        return Context(-1, -1)

    def check(self) -> None:
        self._check_resolved()
        self._check_scope()
        self._check_request_types()

    def _check_resolved(self) -> None:
        for request in self.requests:
            if request.resolver is None:
                self.fail(
                    f"Argname {request.name!r} cannot be resolved.",
                    context=request.context if request.source == "argument" else self.dummy_context,
                    code=MISSING_ARGNAME,
                )
                self._check_unmarked_fixture(request.name)

    def _check_unmarked_fixture(self, fixture_name: str) -> None:
        for module_name in FixtureManager.resolution_sequence(self.module_name):
            result = self.lookup_fullname(
                module_name.push_back(fixture_name),
                context=None,
                predicate=cast(
                    Callable[[Any], TypeGuard[FuncDef]], lambda node: isinstance(node, FuncDef)
                ),
            )
            if result is not None:
                module, node = result
                if isinstance(node.type, CallableType):
                    self.checker.msg.note(
                        f"{fixture_name!r} is defined in '{module_name}', but not marked as a fixture.",
                        context=node,
                        file=module.path,
                    )

    def _check_scope(self) -> None:
        for request in self.requests:
            if (
                isinstance(request.resolver, Fixture)
                and request.scope > request.resolver.scope
                and FixtureScope.unknown
                not in [
                    request.scope,
                    request.resolver.scope,
                ]
            ):
                self.checker.msg.fail(
                    f"{request.source_name!r} (scope={request.scope.name!r}) requests {request.name!r} (scope={request.resolver.scope.name!r}).",
                    context=request.context,
                    file=request.file,
                    code=INVERTED_FIXTURE_SCOPE,
                )

    def _check_request_types(self) -> None:
        for request in self.requests:
            if isinstance(request.resolver, Fixture) and not is_subtype(
                request.resolver.return_type, request.type_
            ):
                self.checker.msg.fail(
                    f"{request.source_name!r} requests {request.name!r} with type {format_type(request.resolver.return_type, self.options)}, but expects type {format_type(request.type_, self.options)}. "
                    f"This happens when executing {self.name!r}.",
                    context=request.context,
                    file=request.file,
                    code=FIXTURE_ARGUMENT_TYPE,
                )
