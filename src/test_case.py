from dataclasses import dataclass

from mypy.nodes import Expression, ListExpr, TupleExpr

from .test_signature import TestSignature


@dataclass(frozen=True, slots=True)
class TestCase:
    node: Expression

    @property
    def is_sequence(self) -> bool:
        return isinstance(self.node, TupleExpr | ListExpr)

    def check_many_items_against(self, signature: TestSignature) -> None:
        assert not signature.is_single
        assert isinstance(self.node, TupleExpr | ListExpr)
        signature.check_many_items(self.node)

    def check_entire_against(self, signature: TestSignature) -> None:
        signature.check_test_case(self.node)

    def check_multiple_against(self, signature: TestSignature) -> None:
        if self.is_sequence:
            self.check_many_items_against(signature)
        else:
            self.check_entire_against(signature)

    def check_single_against(self, signature: TestSignature) -> None:
        assert signature.is_single
        signature.check_one_item(self.node)

    def check_against(self, signature: TestSignature) -> None:
        if signature.is_single:
            self.check_single_against(signature)
        else:
            self.check_multiple_against(signature)
