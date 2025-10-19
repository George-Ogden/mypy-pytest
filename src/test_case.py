from dataclasses import dataclass

from mypy.nodes import Expression

from .test_signature import TestSignature


@dataclass
class TestCase:
    node: Expression

    def check_one_item_against(self, signature: TestSignature) -> None:
        assert signature.is_single
        signature.check_one_item(self.node)
