from dataclasses import dataclass

from mypy.nodes import ArgKind
from mypy.types import CallableType, NoneType, Type

from .test_signature import TestSignature


@dataclass(frozen=True, slots=True, kw_only=True)
class OneItemTestSignature(TestSignature):
    arg_name: str
    arg_type: Type

    def __len__(self) -> int:
        return 1

    @property
    def items_signature(self) -> CallableType:
        raise NotImplementedError()

    @property
    def test_case_signature(self) -> CallableType:
        return CallableType(
            arg_types=[self.arg_type],
            arg_names=[self.arg_name],
            arg_kinds=[ArgKind.ARG_POS],
            fallback=self.checker.named_type("builtins.function"),
            ret_type=NoneType(),
        )

    @property
    def sequence_signature(self) -> CallableType:
        arg_type = self.checker.named_generic_type(
            "typing.Iterable",
            args=[self.arg_type],
        )
        return self._one_unnamed_arg_fn(arg_type)
