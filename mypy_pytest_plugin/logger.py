from pathlib import Path
from typing import ClassVar

from mypy.errorcodes import ErrorCode

from .error_info import ErrorInfo, ExtendedContext


class Logger:
    _errors: ClassVar[dict[Path, list[ErrorInfo]]] = {}

    @classmethod
    def error(
        cls, message: str, *, context: ExtendedContext, code: ErrorCode | None = None
    ) -> None:
        cls._record_error(ErrorInfo(message, context=context, code=code, severity="error"))

    @classmethod
    def _record_error(cls, error: ErrorInfo) -> None:
        if error.context.path not in cls._errors:
            cls._errors[error.context.path] = []
        cls._errors[error.context.path].append(error)

    @classmethod
    def messages(cls) -> str:
        return "\n".join(str(error) for errors in cls._errors.values() for error in errors)
