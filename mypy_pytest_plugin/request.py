from collections.abc import Sequence
from dataclasses import KW_ONLY, dataclass, field
from pathlib import Path
from typing import Literal

from mypy.types import Type, TypeVarLikeType

from .error_info import ExtendedContext
from .test_argument import TestArgument


@dataclass(slots=True)
class Request:
    request: TestArgument
    _: KW_ONLY
    path: Path
    source: Literal["argument", "fixture"]
    used: bool = field(default=False, init=False)

    @property
    def name(self) -> str:
        return self.request.name

    @property
    def type_(self) -> Type:
        return self.request.type_

    @property
    def context(self) -> ExtendedContext:
        return ExtendedContext(context=self.request.context, path=self.path)

    @property
    def type_variables(self) -> Sequence[TypeVarLikeType]:
        return self.request.type_variables
