from collections.abc import Callable
import functools
from typing import cast

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Decorator, Expression, MemberExpr, MypyFile
from mypy.options import Options
from mypy.plugin import AttributeContext, FunctionContext, FunctionSigContext, MethodContext, Plugin
from mypy.types import CallableType, FunctionLike, Type

from .defer import DeferralError
from .excluded_test_checker import ExcludedTestChecker
from .fixture import Fixture
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .iterable_sequence_checker import IterableSequenceChecker
from .mark_checker import MarkChecker
from .mock_call_checker import FunctionMockCallChecker, MethodMockCallChecker
from .param_mark_checker import ParamMarkChecker
from .test_body_ranges import TestBodyRanges
from .test_info import TestInfo
from .test_name_checker import TestNameChecker
from .types_module import TYPES_MODULE
from .utils import compose


class PytestPlugin(Plugin):
    def __init__(self, options: Options) -> None:
        for module_pattern in "*.conftest", "conftest":
            options.per_module_options.setdefault(module_pattern, {})["ignore_missing_imports"] = (
                True
            )
        options.per_module_options.setdefault("mypy_pytest_plugin_types.*", {})[
            "disallow_subclassing_any"
        ] = False
        options.preserve_asts = True
        options.follow_untyped_imports = True
        super().__init__(options)

    def get_additional_deps(self, file: MypyFile) -> list[tuple[int, str, int]]:
        deps = [
            self.module_to_dep("typing"),
            self.module_to_dep(TYPES_MODULE),
            self.module_to_dep("_pytest.fixtures"),
        ]
        if TestNameChecker.is_test_file_name(file.name) or file.name == "conftest":
            deps.extend(map(self.module_to_dep, FixtureManager.default_fixture_module_names()))
            deps.extend(
                map(
                    self.module_to_dep,
                    FixtureManager.conftest_names(Fullname.from_string(file.fullname)),
                )
            )
        return deps

    @classmethod
    def module_to_dep(cls, module: str | Fullname) -> tuple[int, str, int]:
        if not isinstance(module, str):
            module = str(module)
        return (10, module, -1)

    def get_attribute_hook(self, fullname: str) -> Callable[[AttributeContext], Type] | None:
        if fullname.startswith("_pytest.mark.structures.MarkGenerator"):
            return self.check_mark
        return None

    @classmethod
    def check_mark(cls, ctx: AttributeContext) -> Type:
        if (
            not ctx.is_lvalue
            and isinstance(checker := ctx.api, TypeChecker)
            and isinstance(expr := ctx.context, MemberExpr)
        ):
            MarkChecker(checker).check_attribute(expr)
        return ctx.default_attr_type

    def get_function_signature_hook(
        self, fullname: str
    ) -> Callable[[FunctionSigContext], FunctionLike] | None:
        if fullname == "_pytest.mark.param":
            return self.inject_param_stub
        return None

    @classmethod
    def inject_param_stub(cls, ctx: FunctionSigContext) -> FunctionLike:
        if isinstance(ctx.api, TypeChecker):
            symbol_table_node = ctx.api.lookup_qualified(f"{TYPES_MODULE}.param")
            type_ = symbol_table_node.type
            assert isinstance(type_, FunctionLike)
            return type_
        return ctx.default_signature

    def check_param_marks(self, ctx: FunctionContext) -> Type:
        if isinstance(ctx.api, TypeChecker) and isinstance(ctx.context, CallExpr):
            ParamMarkChecker(ctx.api).check_param_marks(ctx.context)
        return ctx.default_return_type

    def get_function_hook(self, fullname: str) -> Callable[[FunctionContext], Type] | None:
        if fullname.startswith("unittest.mock"):
            return functools.partial(FunctionMockCallChecker.check_mock_calls, fullname=fullname)
        if fullname == "_pytest.mark.param":
            return self.check_param_marks
        if fullname == "_pytest.fixtures.fixture":
            hook_fn = self.check_pytest_structure
        else:
            hook_fn = self.check_iterable_sequence
        return compose(hook_fn, self.enable_test_attribute)

    def get_method_hook(self, fullname: str) -> Callable[[MethodContext], Type] | None:
        if fullname.startswith("unittest.mock"):
            return functools.partial(MethodMockCallChecker.check_mock_calls, fullname=fullname)
        if (
            fullname.startswith("_pytest.mark.structures") and "Mark" in fullname
        ) or fullname.startswith("_pytest.fixtures.FixtureFunctionMarker"):
            hook_fn = self.check_pytest_structure
        else:
            hook_fn = self.check_iterable_sequence
        return compose(hook_fn, self.enable_test_attribute)

    @classmethod
    def enable_test_attribute[T: MethodContext | FunctionContext](cls, ctx: T) -> T:
        if (
            isinstance(ctx.api, TypeChecker)
            and hasattr(ctx.context, "fullname")
            and TestNameChecker.is_test_fn_name(ctx.context.fullname)
        ):
            cls._update_return_type(ctx.default_return_type, checker=ctx.api)
        return ctx

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
    def check_pytest_structure(cls, ctx: MethodContext | FunctionContext) -> Type:
        try:
            return cls._check_pytest_structure(ctx)
        except DeferralError:
            assert isinstance(ctx.api, TypeChecker)
            ctx.api.defer_node(cast(Decorator, ctx.context), None)
            return ctx.default_return_type

    @classmethod
    def _check_pytest_structure(cls, ctx: MethodContext | FunctionContext) -> Type:
        if isinstance(ctx.context, Decorator) and isinstance(ctx.api, TypeChecker):
            cls._update_return_type(ctx.default_return_type, ctx.api)
            if not Fixture.is_fixture_and_mark(ctx.context, checker=ctx.api):
                if fixture := Fixture.from_decorator(ctx.context, checker=ctx.api):
                    return fixture.as_fixture_type(decorator=ctx.context, checker=ctx.api)
                ignored_testnames = ExcludedTestChecker.ignored_test_names(
                    ctx.api.tree.defs, ctx.api
                )
                if ctx.context.name not in ignored_testnames and TestNameChecker.is_test_name(
                    ctx.context.fullname
                ):
                    cls._check_decorators(ctx.context, ctx.api)
        return ctx.default_return_type

    @classmethod
    def _update_return_type(cls, return_type: Type, checker: TypeChecker) -> None:
        if (
            isinstance(return_type, CallableType)
            and return_type.fallback.type.fullname == "builtins.function"
        ):
            return_type.fallback = checker.named_type(f"{TYPES_MODULE}.Testable")

    @classmethod
    def _check_decorators(cls, decorator: Decorator, checker: TypeChecker) -> None:
        test_info = TestInfo.from_fn_def(decorator, checker=checker)
        if test_info is not None:
            test_info.check()


def plugin(version: str) -> type[PytestPlugin]:
    return PytestPlugin
