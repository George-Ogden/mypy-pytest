from dataclasses import KW_ONLY, dataclass, field
from typing import Literal

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
