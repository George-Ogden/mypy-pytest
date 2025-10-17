from dataclasses import dataclass

from mypy.checker import TypeChecker
import mypy.nodes
from mypy.types import CallableType, Instance, NoneType, TupleType, Type


@dataclass(frozen=True, slots=True, kw_only=True)
class TestSignature:
    checker: TypeChecker
    fn_name: str
    arg_names: tuple[str, ...]
    arg_types: tuple[Type, ...]

    def __post_init__(self) -> None:
        assert len(self.arg_names) == len(self.arg_types)

    def __len__(self) -> int:
        return len(self.arg_names)

    @property
    def items_signature(self) -> CallableType:
        return CallableType(
            arg_types=self.arg_types,
            arg_names=self.arg_names,
            arg_kinds=[mypy.nodes.ArgKind.ARG_POS] * len(self),
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
        )

    def _one_unnamed_arg_fn(self, arg_type: Type) -> CallableType:
        return CallableType(
            arg_types=[arg_type],
            arg_names=[None],
            arg_kinds=[mypy.nodes.ArgKind.ARG_POS],
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
        )

    def _test_case_arg_type(self) -> TupleType:
        return TupleType(list(self.arg_types), fallback=self.checker.named_type("builtins.tuple"))

    @property
    def test_case_signature(self) -> CallableType:
        return self._one_unnamed_arg_fn(self._test_case_arg_type())

    def _single_sequence_arg_type(self) -> Instance:
        [arg_type] = self.arg_types
        return self.checker.named_generic_type(
            "typing.Iterable",
            args=[arg_type],
        )

    def _multiple_sequence_arg_type(self) -> Instance:
        return self.checker.named_generic_type(
            "typing.Iterable",
            args=[self._test_case_arg_type()],
        )

    @property
    def sequence_signature(self) -> CallableType:
        if len(self) == 1:
            return self._single_sequence_signature
        else:
            return self._multiple_sequence_signature

    @property
    def _single_sequence_signature(self) -> CallableType:
        return self._one_unnamed_arg_fn(self._single_sequence_arg_type())

    @property
    def _multiple_sequence_signature(self) -> CallableType:
        return self._one_unnamed_arg_fn(self._multiple_sequence_arg_type())

    def _check_call(
        self, callee: CallableType, args: list[mypy.nodes.Expression], node: mypy.nodes.Context
    ) -> None:
        self.checker.expr_checker.check_call(
            callee=callee,
            args=args,
            arg_kinds=[mypy.nodes.ArgKind.ARG_POS] * len(args),
            context=node,
            callable_name=self.fn_name,
        )

    def check_one_item(self, node: mypy.nodes.Expression) -> None:
        self._check_call(self.items_signature, [node], node)

    def check_many_items(self, node: mypy.nodes.TupleExpr | mypy.nodes.ListExpr) -> None:
        self._check_call(self.items_signature, node.items, node)

    def check_test_case(self, node: mypy.nodes.Expression) -> None:
        assert len(self) != 1
        self._check_call(self.test_case_signature, [node], node)

    def check_sequence(self, node: mypy.nodes.Expression) -> None:
        self._check_call(self.sequence_signature, [node], node)
