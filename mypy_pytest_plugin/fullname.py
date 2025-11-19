from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class Fullname:
    _parts: tuple[str, ...]

    @classmethod
    def from_string(cls, fullname: str) -> Self:
        if fullname:
            return cls(tuple(fullname.split(".")))
        return cls(())

    def __str__(self) -> str:
        return ".".join(self._parts)

    def __bool__(self) -> bool:
        return bool(self._parts)

    def push_back(self, extra: str) -> Self:
        return type(self)((*self._parts, extra))

    @property
    def name(self) -> str:
        return self._parts[-1]

    @property
    def module_name(self) -> Self:
        return type(self)(self._parts[:-1])

    def __lt__(self, other: Self) -> bool:
        if isinstance(other, type(self)):
            return self._parts < other._parts
        return NotImplemented
