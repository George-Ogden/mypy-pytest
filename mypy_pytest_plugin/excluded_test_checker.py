from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import itertools

from mypy.checker import TypeChecker
from mypy.nodes import (
    AssignmentStmt,
    Expression,
    MemberExpr,
    NameExpr,
    Statement,
)
from mypy.subtypes import is_same_type
from mypy.types import LiteralType

from .checker_wrapper import CheckerWrapper
from .defer import DeferralError, DeferralReason
from .fullname import Fullname
from .test_name_checker import TestNameChecker


@dataclass(frozen=True, eq=False)
class ExcludedTestChecker(CheckerWrapper):
    checker: TypeChecker

    @classmethod
    def is_test(cls, fullname: str, checker: TypeChecker) -> bool:
        ignored_testnames = cls(checker).ignored_test_names(checker.tree.defs)
        return Fullname.from_string(
            fullname
        ).name not in ignored_testnames and TestNameChecker.is_test_name(fullname)

    def ignored_test_names(self, defs: Sequence[Statement]) -> set[str]:
        return self._ignored_test_names_from_statements(defs)

    def _ignored_test_names_from_statements(self, statements: Sequence[Statement]) -> set[str]:
        return self._ignored_test_names_from_assignments(
            [statement for statement in statements if isinstance(statement, AssignmentStmt)],
        )

    def _ignored_test_names_from_assignments(
        self, assignments: Sequence[AssignmentStmt]
    ) -> set[str]:
        return set(
            itertools.chain.from_iterable(
                self._identify_non_test_assignment_names(assignment) for assignment in assignments
            )
        )

    def _identify_non_test_assignment_names(self, assignment: AssignmentStmt) -> Iterable[str]:
        rvalue_type = self.checker.lookup_type_or_none(assignment.rvalue)
        if rvalue_type is None:
            raise DeferralError(DeferralReason.REQUIRED_WAIT)
        if is_same_type(rvalue_type, LiteralType(False, self.checker.named_type("builtins.bool"))):
            for lvalue in assignment.lvalues:
                assignment_target = self._test_assignment_target(lvalue)
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
