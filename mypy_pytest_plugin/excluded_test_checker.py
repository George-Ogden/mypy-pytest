from collections.abc import Iterable, Sequence
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

from .defer import DeferralError


class ExcludedTestChecker:
    @classmethod
    def ignored_test_names(cls, defs: Sequence[Statement], checker: TypeChecker) -> set[str]:
        return cls._ignored_test_names_from_statements(defs, checker)

    @classmethod
    def _ignored_test_names_from_statements(
        cls, statements: Sequence[Statement], checker: TypeChecker
    ) -> set[str]:
        return cls._ignored_test_names_from_assignments(
            [statement for statement in statements if isinstance(statement, AssignmentStmt)],
            checker=checker,
        )

    @classmethod
    def _ignored_test_names_from_assignments(
        cls, assignments: Sequence[AssignmentStmt], checker: TypeChecker
    ) -> set[str]:
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
        rvalue_type = checker.lookup_type_or_none(assignment.rvalue)
        if rvalue_type is None:
            raise DeferralError()
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
