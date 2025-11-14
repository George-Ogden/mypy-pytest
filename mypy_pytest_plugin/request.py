from dataclasses import dataclass, field

from .test_argument import TestArgument


@dataclass(slots=True)
class Request:
    request: TestArgument
    seen: bool = field(default=False, init=False)
