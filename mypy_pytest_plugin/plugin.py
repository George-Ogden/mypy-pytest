from collections.abc import Callable
from typing import Final, cast

from mypy.checker import TypeChecker
from mypy.nodes import (
    CallExpr,
    Decorator,
    Expression,
    MypyFile,
)
from mypy.plugin import FunctionContext, MethodContext, Plugin
from mypy.types import CallableType, Type

from .defer import DeferralError
from .excluded_test_checker import ExcludedTestChecker
from .fixture import Fixture
from .iterable_sequence_checker import IterableSequenceChecker
from .test_body_ranges import TestBodyRanges
from .test_info import TestInfo
from .test_name_checker import TestNameChecker


class PytestPlugin(Plugin):
    TYPES_MODULE: Final[str] = "mypy_pytest_plugin_types"

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        deps = [
            (10, "typing", -1),
            (10, self.TYPES_MODULE, -1),
        ]
        return deps

    def get_function_hook(self, fullname: str) -> Callable[[FunctionContext], Type] | None:
        return self.check_iterable_sequence

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if (
            fullname.startswith("_pytest.mark.structures") and "Mark" in fullname
        ) or fullname.startswith("_pytest.fixtures.FixtureFunctionMarker"):
            return self.check_pytest_structure
        return self.check_iterable_sequence

    @classmethod
    def check_iterable_sequence(cls, ctx: MethodContext | FunctionContext) -> Type:
        if (
            isinstance(ctx.context, CallExpr)
            and isinstance(ctx.api, TypeChecker)
            and TestNameChecker.is_test_file_name(ctx.api.tree.fullname)
            and ctx.context.line in TestBodyRanges.from_defs(ctx.api.tree.defs)
            and all(cls._is_real_argument(arg) for arg in ctx.context.args)
        ):
            IterableSequenceChecker(ctx.api).check_iterable_sequence_call(ctx.context)
        return ctx.default_return_type

    @classmethod
    def _is_real_argument(cls, argument: Expression) -> bool:
        return argument.line != -1 and argument.end_line is not None

    @classmethod
    def check_pytest_structure(cls, ctx: MethodContext) -> Type:
        try:
            return cls._check_pytest_structure(ctx)
        except DeferralError:
            assert isinstance(ctx.api, TypeChecker)
            ctx.api.defer_node(cast(Decorator, ctx.context), None)
            return ctx.default_return_type

    @classmethod
    def _check_pytest_structure(cls, ctx: MethodContext) -> Type:
        if isinstance(ctx.context, Decorator) and isinstance(ctx.api, TypeChecker):
            cls._update_return_type(ctx.default_return_type, ctx.api)
            if not Fixture.is_fixture_and_mark(
                ctx.context, checker=ctx.api
            ) and not Fixture.from_decorator(ctx.context, checker=ctx.api):
                ignored_testnames = ExcludedTestChecker.ignored_test_names(
                    ctx.api.tree.defs, ctx.api
                )
                if ctx.context.name not in ignored_testnames and TestNameChecker.is_test_name(
                    ctx.context.fullname
                ):
                    cls._check_decorators(ctx.context, ctx.api)
        return ctx.default_return_type

    @classmethod
    def _check_decorators(cls, node: Decorator, checker: TypeChecker) -> None:
        test_info = TestInfo.from_fn_def(node, checker=checker)
        if test_info is not None:
            test_info.check()

    @classmethod
    def _update_return_type(cls, return_type: Type, checker: TypeChecker) -> None:
        if (
            isinstance(return_type, CallableType)
            and return_type.fallback.type.fullname == "builtins.function"
        ):
            return_type.fallback = checker.named_type(f"{cls.TYPES_MODULE}.Testable")


def plugin(version: str) -> type[PytestPlugin]:
    return PytestPlugin
