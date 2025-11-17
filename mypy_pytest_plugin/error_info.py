from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from typing import Literal

from mypy.errorcodes import ErrorCode
from mypy.nodes import Context


@dataclass(frozen=True, slots=True, kw_only=True, repr=True)
class ExtendedContext:
    context: Context
    file: Path

    def __str__(self) -> str:
        suffix = "" if self.context.line < 0 else f"{self.context.line}:"
        return f"{self.file}{suffix}"


@dataclass(frozen=True, slots=True, repr=True)
class ErrorInfo:
    message: str
    _: KW_ONLY
    context: ExtendedContext
    severity: Literal["error", "info"]
    code: ErrorCode | None

    def __str__(self) -> str:
        suffix = "" if self.code is None else f" [{self.code.code}]"
        return f"{self.context}: {self.message}{suffix}"
