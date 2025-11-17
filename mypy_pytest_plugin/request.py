from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass, field
from typing import Literal

from mypy.nodes import Context
from mypy.types import Type, TypeVarLikeType

from .test_argument import TestArgument


@dataclass(slots=True)
class Request:
    request: TestArgument
    _: KW_ONLY
    source: Literal["argument", "fixture"]
    used: bool = field(default=False, init=False)

    @property
    def name(self) -> str:
        return self.request.name

    @property
    def type_(self) -> Type:
        return self.request.type_

    @property
    def context(self) -> Context:
        return self.request.context

    @property
    def type_variables(self) -> Sequence[TypeVarLikeType]:
        return self.request.type_variables
