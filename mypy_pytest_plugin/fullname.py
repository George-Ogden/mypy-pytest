from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Fullname:
    _parts: tuple[str, ...]

    def __init__(self, *parts: str) -> None:
        object.__setattr__(self, "_parts", parts)

    @classmethod
    def from_string(cls, fullname: str) -> Self:
        if fullname:
            return cls(*fullname.split("."))
        return cls()

    def __str__(self) -> str:
        return ".".join(self._parts)

    def _repr__(self) -> str:
        return f"{type(self).__name__}({self})"

    def pop_back(self) -> tuple[str, Self]:
        return self._parts[-1], type(self)(*self._parts[:-1])
