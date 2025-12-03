from dataclasses import dataclass

from mypy.nodes import ArgKind, CallExpr, Expression, ListExpr, RefExpr, TupleExpr

from .test_signature import TestSignature


@dataclass(frozen=True, slots=True)
class TestCase:
    expr: Expression

    @property
    def positional_args(self) -> list[Expression]:
        assert isinstance(self.expr, CallExpr)
        return [
            arg
            for arg, arg_kind in zip(self.expr.args, self.expr.arg_kinds, strict=True)
            if arg_kind is ArgKind.ARG_POS
        ]

    def check_param_against(self, signature: TestSignature) -> None:
        signature.check_items(self.positional_args, context=self.expr)

    def check_items_against(self, signature: TestSignature) -> None:
        assert isinstance(self.expr, TupleExpr | ListExpr)
        signature.check_items(self.expr.items, context=self.expr)

    def check_entire_against(self, signature: TestSignature) -> None:
        signature.check_test_case(self.expr)

    def check_against(self, signature: TestSignature) -> None:
        if self.is_param:
            self.check_param_against(signature)
        elif signature.is_single or not self.is_sequence:
            self.check_entire_against(signature)
        else:
            self.check_items_against(signature)

    @property
    def is_param(self) -> bool:
        return (
            isinstance(self.expr, CallExpr)
            and isinstance(self.expr.callee, RefExpr)
            and self.expr.callee.fullname == "_pytest.mark.param"
            and all(
                arg_kind in (ArgKind.ARG_POS, ArgKind.ARG_NAMED) for arg_kind in self.expr.arg_kinds
            )
        )

    @property
    def is_sequence(self) -> bool:
        return isinstance(self.expr, TupleExpr | ListExpr)
