import abc

from mypy.checker import TypeChecker
from mypy.errorcodes import ErrorCode
from mypy.nodes import Context


class CheckerWrapper(abc.ABC):
    checker: TypeChecker

    @abc.abstractmethod
    def __init__(self) -> None: ...

    def fail(self, msg: str, *, context: Context, code: ErrorCode) -> None:
        self.checker.fail(msg, context=context, code=code)

    def note(self, msg: str, *, context: Context, code: ErrorCode) -> None:
        self.checker.note(msg, context=context, code=code)
