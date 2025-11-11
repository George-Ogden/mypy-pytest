from collections.abc import Callable, Iterable, Sequence
import fnmatch
import functools
import itertools
from pathlib import Path
from typing import Final, cast

from _pytest.config import get_config
from _pytest.main import Session
from _pytest.pathlib import fnmatch_ex
from mypy.checker import TypeChecker
from mypy.nodes import (
    AssignmentStmt,
    Decorator,
    Expression,
    MemberExpr,
    MypyFile,
    NameExpr,
    Statement,
    TypeInfo,
)
from mypy.plugin import MethodContext, Plugin
from mypy.subtypes import is_same_type
from mypy.types import CallableType, Instance, LiteralType, Type

from .test_info import TestInfo


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
            ignored_testnames = cls._ignored_test_names_from_statements(ctx.api.tree.defs, ctx.api)
            if ignored_testnames is None:
                ctx.api.defer_node(ctx.context, None)
            elif ctx.context.name not in ignored_testnames and cls.is_test_fn_name(
                ctx.context.fullname
            ):
                cls._check_decorators(ctx.context, ctx.api)
            cls._update_return_type(ctx.default_return_type, ctx.api)
        return ctx.default_return_type

    @classmethod
    def _ignored_test_names_from_statements(
        cls, statements: Sequence[Statement], checker: TypeChecker
    ) -> set[str] | None:
        return cls._ignored_test_names_from_assignments(
            [statement for statement in statements if isinstance(statement, AssignmentStmt)],
            checker=checker,
        )

    @classmethod
    def _ignored_test_names_from_assignments(
        cls, assignments: Sequence[AssignmentStmt], checker: TypeChecker
    ) -> set[str] | None:
        if cls._any_unresolved_types((assignment.rvalue for assignment in assignments), checker):
            return None
        return set(
            itertools.chain.from_iterable(
                cls._identify_non_test_assignment_names(assignment, checker)
                for assignment in assignments
            )
        )

    @classmethod
    def _identify_non_test_assignment_names(
        cls, assignment: AssignmentStmt, checker: TypeChecker
    ) -> Iterable[str]:
        rvalue_type = checker.lookup_type(assignment.rvalue)
        if is_same_type(rvalue_type, LiteralType(False, checker.named_type("builtins.bool"))):
            for lvalue in assignment.lvalues:
                assignment_target = cls._test_assignment_target(lvalue)
                if assignment_target is not None:
                    yield assignment_target

    @classmethod
    def _test_assignment_target(cls, expression: Expression) -> str | None:
        if (
            isinstance(expression, MemberExpr)
            and isinstance(expression.expr, NameExpr)
            and expression.name == "__test__"
        ):
            return expression.expr.name
        return None

    @classmethod
    def _any_unresolved_types(cls, expressions: Iterable[Expression], checker: TypeChecker) -> bool:
        return any(checker.lookup_type_or_none(expression) is None for expression in expressions)

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

    @classmethod
    def is_test_fn_name(cls, fullname: str) -> bool:
        path, function = cls._split_fullname(fullname)
        return cls.path_match(path) and cls.fn_match(function)

    @classmethod
    def _split_fullname(cls, fullname: str) -> tuple[Path, str]:
        [*path, name] = fullname.split(".")
        if path:
            path[-1] += ".py"
        return Path(*path), name

    @classmethod
    @functools.cache
    def session(cls) -> Session:
        config = get_config()
        config.parse([])
        return Session.from_config(config)

    @classmethod
    @functools.cache
    def file_patterns(cls) -> list[str]:
        return cls.session().config.getini("python_files")

    @classmethod
    @functools.cache
    def fn_patterns(cls) -> list[str]:
        return cls.session().config.getini("python_functions")

    @classmethod
    @functools.cache
    def path_match(cls, path: Path) -> bool:
        return any(fnmatch_ex(pattern, path) for pattern in cls.file_patterns())

    @classmethod
    def fn_match(cls, fn_name: str) -> bool:
        return any(
            fn_name.startswith(pattern) or fnmatch.fnmatch(pattern, fn_name)
            for pattern in cls.fn_patterns()
        )


def plugin(version: str) -> type[PytestPlugin]:
    return PytestPlugin
