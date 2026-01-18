from dataclasses import dataclass

from mypy.nodes import ArgKind
from mypy.subtypes import is_same_type
from mypy.types import CallableType, NoneType, Type, UnionType

from .test_signature import TestSignature
from .types_module import TYPES_MODULE


@dataclass(frozen=True, slots=True, kw_only=True)
class OneItemTestSignature(TestSignature):
    arg_name: str
    arg_type: Type

    def __eq__(self, other: object) -> bool:
        return (
            self._equal_names(other)
            and self.arg_name == other.arg_name
            and is_same_type(self.arg_type, other.arg_type)
        )

    def __len__(self) -> int:
        return 1

    @property
    def items_signature(self) -> CallableType:
        return CallableType(
            arg_types=[self.arg_type],
            arg_names=[self.arg_name],
            arg_kinds=[ArgKind.ARG_POS],
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
            variables=self.type_variables,
        )

    @property
    def signature_type(self) -> Type:
        return UnionType(
            [
                self.arg_type,
                self.checker.named_generic_type(f"{TYPES_MODULE}.ParameterSet", [self.arg_type]),
            ]
        )

    @property
    def test_case_signature(self) -> CallableType:
        return CallableType(
            arg_types=[self.signature_type],
            arg_names=[self.arg_name],
            arg_kinds=[ArgKind.ARG_POS],
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
            variables=self.type_variables,
        )

    @property
    def sequence_signature(self) -> CallableType:
        arg_type = self.checker.named_generic_type("typing.Iterable", args=[self.signature_type])
        return self._one_unnamed_arg_fn(arg_type)
