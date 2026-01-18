import abc
from dataclasses import dataclass
import keyword

from mypy.checker import TypeChecker
from mypy.nodes import (
    Context,
    Expression,
    StrExpr,
)

from .checker_wrapper import CheckerWrapper


@dataclass(frozen=True)
class NamesParser(CheckerWrapper):
    checker: TypeChecker

    def _check_valid_identifier(self, name: str, context: StrExpr) -> bool:
        if not (valid_identifier := name.isidentifier()):
            self._fail_invalid_identifier(name, context)
        elif not (valid_identifier := (not keyword.iskeyword(name))):
            self._fail_keyword_identifier(name, context)
        elif not (valid_identifier := (name != "request")):
            self._fail_request_identifier(name, context)
        return valid_identifier

    def parse_name(self, expression: Expression) -> str | None:
        if isinstance(expression, StrExpr):
            name = expression.value
            if self._check_valid_identifier(name, expression):
                return name
        else:
            self._fail_unreadable_identifier(expression)
        return None

    @abc.abstractmethod
    def _fail_invalid_identifier(self, name: str, context: Context) -> None: ...

    @abc.abstractmethod
    def _fail_keyword_identifier(self, name: str, context: Context) -> None: ...

    @abc.abstractmethod
    def _fail_request_identifier(self, name: str, context: Context) -> None: ...

    @abc.abstractmethod
    def _fail_unreadable_identifier(self, context: Context) -> None: ...
