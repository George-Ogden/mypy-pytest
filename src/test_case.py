from dataclasses import dataclass

from mypy.nodes import Expression, ListExpr, TupleExpr

from .test_signature import TestSignature


@dataclass(frozen=True, slots=True)
class TestCase:
    node: Expression

    @property
    def is_sequence(self) -> bool:
        return isinstance(self.node, TupleExpr | ListExpr)

    def check_items_against(self, signature: TestSignature) -> None:
        assert isinstance(self.node, TupleExpr | ListExpr)
        signature.check_items(self.node)

    def check_entire_against(self, signature: TestSignature) -> None:
        signature.check_test_case(self.node)

    def check_against(self, signature: TestSignature) -> None:
        if signature.is_single or not self.is_sequence:
            self.check_entire_against(signature)
        else:
            self.check_items_against(signature)
