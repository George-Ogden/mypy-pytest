from collections.abc import Sequence
from dataclasses import dataclass

from mypy.nodes import ArgKind
from mypy.subtypes import is_same_type
from mypy.types import CallableType, NoneType, TupleType, Type

from .test_signature import TestSignature


@dataclass(frozen=True, slots=True, kw_only=True)
class ManyItemsTestSignature(TestSignature):
    arg_names: Sequence[str]
    arg_types: Sequence[Type]

    def __eq__(self, other: object) -> bool:
        return (
            self._equal_names(other)
            and self._as_dict().keys() == other._as_dict().keys()
            and all(
                is_same_type(self._as_dict()[key], other._as_dict()[key])
                for key in self._as_dict().keys()
            )
        )

    def _as_dict(self) -> dict[str, Type]:
        return dict(zip(self.arg_names, self.arg_types, strict=True))

    def __post_init__(self) -> None:
        assert len(self.arg_names) == len(self.arg_types)

    def __len__(self) -> int:
        return len(self.arg_names)

    @property
    def items_signature(self) -> CallableType:
        return CallableType(
            arg_types=self.arg_types,
            arg_names=self.arg_names,
            arg_kinds=[ArgKind.ARG_POS] * len(self),
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
            variables=self.type_variables,
        )

    def _test_case_arg_type(self) -> TupleType:
        return TupleType(list(self.arg_types), fallback=self.checker.named_type("builtins.tuple"))

    @property
    def test_case_signature(self) -> CallableType:
        return self._one_unnamed_arg_fn(self._test_case_arg_type())

    @property
    def sequence_signature(self) -> CallableType:
        arg_type = self.checker.named_generic_type(
            "typing.Iterable",
            args=[self._test_case_arg_type()],
        )
        return self._one_unnamed_arg_fn(arg_type)
