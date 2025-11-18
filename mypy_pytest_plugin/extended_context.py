from dataclasses import dataclass
from typing import Self

from mypy.checker import TypeChecker
from mypy.nodes import Context


@dataclass(frozen=True, slots=True, kw_only=True)
class ExtendedContext:
    context: Context
    file: str

    @classmethod
    def from_context(cls, context: Context, checker: TypeChecker) -> Self:
        return cls(context=context, file=checker.path)
