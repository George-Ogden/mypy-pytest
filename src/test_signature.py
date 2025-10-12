from dataclasses import dataclass

from mypy.checker import TypeChecker
import mypy.nodes
from mypy.types import CallableType, Instance, NoneType, TupleType, Type


@dataclass(frozen=True, slots=True, kw_only=True)
class TestSignature:
    checker: TypeChecker
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

    def _single_unnamed_arg_fn(self, arg_type: Type) -> CallableType:
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
        return self._single_unnamed_arg_fn(self._test_case_arg_type())

    def _sequence_arg_type(self) -> Instance:
        return self.checker.named_generic_type(
            "typing.Iterable",
            args=[
                TupleType(list(self.arg_types), fallback=self.checker.named_type("builtins.tuple"))
            ],
        )

    @property
    def sequence_signature(self) -> CallableType:
        return CallableType(
            arg_types=[self._sequence_arg_type()],
            arg_names=[None],
            arg_kinds=[mypy.nodes.ArgKind.ARG_POS],
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
        )
