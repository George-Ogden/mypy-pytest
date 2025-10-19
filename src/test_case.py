from dataclasses import dataclass

from mypy.nodes import Expression, ListExpr, TupleExpr

from .test_signature import TestSignature


@dataclass
class TestCase:
    node: Expression

    def check_one_item_against(self, signature: TestSignature) -> None:
        assert signature.is_single
        signature.check_one_item(self.node)

    def check_many_items_against(self, signature: TestSignature) -> None:
        assert not signature.is_single
        assert isinstance(self.node, TupleExpr | ListExpr)
        signature.check_many_items(self.node)

    def check_entire_against(self, signature: TestSignature) -> None:
        signature.check_test_case(self.node)
