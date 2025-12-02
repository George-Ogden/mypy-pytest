import abc
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self, TypeGuard, cast

from mypy.checker import TypeChecker
from mypy.nodes import ArgKind, Context, Expression
from mypy.types import CallableType, NoneType, Type, TypeVarLikeType


@dataclass(frozen=True, slots=True, kw_only=True)
class TestSignature(abc.ABC):
    checker: TypeChecker
    fn_name: str
    type_variables: Sequence[TypeVarLikeType]

    def _equal_names(self, other: object) -> TypeGuard[Self]:
        return type(other) is type(self) and self.fn_name == cast(Self, other).fn_name

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
            variables=self.type_variables,
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

    def _check_call(self, callee: CallableType, args: list[Expression], context: Context) -> None:
        self.checker.expr_checker.check_call(
            callee=callee,
            args=args,
            arg_kinds=[ArgKind.ARG_POS] * len(args),
            context=context,
            callable_name=self.fn_name,
        )

    def check_items(self, items: list[Expression], *, context: Context) -> None:
        self._check_call(self.items_signature, items, context)

    def check_test_case(self, expr: Expression) -> None:
        self._check_call(self.test_case_signature, [expr], expr)

    def check_sequence(self, expr: Expression) -> None:
        self._check_call(self.sequence_signature, [expr], expr)
