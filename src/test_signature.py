import abc
from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.nodes import ArgKind, Context, Expression, ListExpr, TupleExpr
from mypy.types import CallableType, NoneType, Type


@dataclass(frozen=True, slots=True, kw_only=True)
class TestSignature(abc.ABC):
    checker: TypeChecker
    fn_name: str

    @abc.abstractmethod
    def __len__(self) -> int: ...

    @property
    def is_single(self) -> bool:
        return len(self) == 1

    def _one_unnamed_arg_fn(self, arg_type: Type) -> CallableType:
        return CallableType(
            arg_types=[arg_type],
            arg_names=[None],
            arg_kinds=[ArgKind.ARG_POS],
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
        )

    @property
    @abc.abstractmethod
    def sequence_signature(self) -> CallableType: ...

    @property
    @abc.abstractmethod
    def test_case_signature(self) -> CallableType: ...

    @property
    @abc.abstractmethod
    def items_signature(self) -> CallableType: ...

    def _check_call(self, callee: CallableType, args: list[Expression], node: Context) -> None:
        self.checker.expr_checker.check_call(
            callee=callee,
            args=args,
            arg_kinds=[ArgKind.ARG_POS] * len(args),
            context=node,
            callable_name=self.fn_name,
        )

    def check_items(self, node: TupleExpr | ListExpr) -> None:
        self._check_call(self.items_signature, node.items, node)

    def check_test_case(self, node: Expression) -> None:
        self._check_call(self.test_case_signature, [node], node)

    def check_sequence(self, node: Expression) -> None:
        self._check_call(self.sequence_signature, [node], node)
