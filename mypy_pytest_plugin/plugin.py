from collections.abc import Callable
from typing import Final, cast

from mypy.checker import TypeChecker
from mypy.nodes import (
    Decorator,
    MypyFile,
    TypeInfo,
)
from mypy.plugin import MethodContext, Plugin
from mypy.types import CallableType, Instance, Type

from .excluded_test_checker import ExcludedTestChecker
from .test_info import TestInfo
from .test_name_checker import TestNameChecker


class PytestPlugin(Plugin):
    TYPES_MODULE: Final[str] = "mypy_pytest_plugin_types"

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        return [(10, "typing", -1), (10, self.TYPES_MODULE, -1)]

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if fullname.startswith("_pytest.mark.structures"):
            return self.check
        return None

    @classmethod
    def check(cls, ctx: MethodContext) -> Type:
        if isinstance(ctx.context, Decorator) and isinstance(ctx.api, TypeChecker):
            ignored_testnames = ExcludedTestChecker.ignored_test_names(ctx.api.tree.defs, ctx.api)
            if ignored_testnames is None:
                ctx.api.defer_node(ctx.context, None)
            elif ctx.context.name not in ignored_testnames and TestNameChecker.is_test_name(
                ctx.context.fullname
            ):
                cls._check_decorators(ctx.context, ctx.api)
            cls._update_return_type(ctx.default_return_type, ctx.api)
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
            testable_symbol_table_node = checker.modules[cls.TYPES_MODULE].names[
                "Testable"
            ]  # direct lookup not working
            return_type.fallback = Instance(cast(TypeInfo, testable_symbol_table_node.node), [])


def plugin(version: str) -> type[PytestPlugin]:
    return PytestPlugin
