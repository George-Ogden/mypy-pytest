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

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self})"

    def __bool__(self) -> bool:
        return bool(self._parts)

    def pop_back(self) -> tuple[str, Self]:
        return self.back, type(self)(*self._parts[:-1])

    def push_back(self, extra: str) -> Self:
        return type(self)(*self._parts, extra)

    @property
    def back(self) -> str:
        return self._parts[-1]

    def __lt__(self, other: Self) -> bool:
        if isinstance(other, type(self)):
            return self._parts < other._parts
        return NotImplemented
