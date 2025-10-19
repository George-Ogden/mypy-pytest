from collections.abc import Iterator
from dataclasses import dataclass

from mypy.nodes import Expression, ListExpr, SetExpr, TupleExpr

from .test_case import TestCase
from .test_signature import TestSignature


@dataclass(frozen=True, slots=True)
class Argvals:
    node: Expression

    def __iter__(self) -> Iterator[TestCase]:
        assert isinstance(self.node, SetExpr | ListExpr | TupleExpr)
        for item in self.node.items:
            yield TestCase(item)

    def check_sequence_against(self, signature: TestSignature) -> None:
        for test_case in self:
            test_case.check_against(signature)
