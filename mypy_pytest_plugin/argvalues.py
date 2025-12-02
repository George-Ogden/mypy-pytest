from collections.abc import Iterator
from dataclasses import dataclass

from mypy.nodes import Expression, ListExpr, SetExpr, StarExpr, TupleExpr

from .test_case import TestCase
from .test_signature import TestSignature


@dataclass(frozen=True, slots=True)
class Argvalues:
    expr: Expression

    def __iter__(self) -> Iterator[TestCase]:
        assert isinstance(self.expr, SetExpr | ListExpr | TupleExpr)
        for item in self.expr.items:
            yield TestCase(item)

    def check_sequence_against(self, signature: TestSignature) -> None:
        for test_case in self:
            test_case.check_against(signature)

    def check_entire_against(self, signature: TestSignature) -> None:
        signature.check_sequence(self.expr)

    def check_against(self, signature: TestSignature) -> None:
        if self.is_ordered_sequence:
            self.check_sequence_against(signature)
        else:
            self.check_entire_against(signature)

    @property
    def is_ordered_sequence(self) -> bool:
        return isinstance(self.expr, SetExpr | ListExpr | TupleExpr) and not any(
            isinstance(item, StarExpr) for item in self.expr.items
        )
