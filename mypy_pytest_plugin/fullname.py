from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Fullname:
    parts: tuple[str, ...]

    def __init__(self, *parts: str) -> None:
        object.__setattr__(self, "parts", parts)

    @classmethod
    def from_string(cls, fullname: str) -> Self:
        if fullname:
            return cls(*fullname.split("."))
        return cls()

    def __str__(self) -> str:
        return ".".join(self.parts)
