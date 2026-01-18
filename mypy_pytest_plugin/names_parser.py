import abc
from dataclasses import dataclass
import keyword

from mypy.checker import TypeChecker
from mypy.nodes import Context, Expression, StrExpr
from mypy.types import LiteralType, Type

from .checker_wrapper import CheckerWrapper
from .defer import DeferralError, DeferralReason


@dataclass(frozen=True)
class NamesParser(CheckerWrapper):
    checker: TypeChecker

    def _check_valid_identifier(self, name: str, context: Context) -> bool:
        if not (valid_identifier := name.isidentifier()):
            self._fail_invalid_identifier(name, context)
        elif not (valid_identifier := (not keyword.iskeyword(name))):
            self._fail_keyword_identifier(name, context)
        elif not (valid_identifier := (name != "request")):
            self._fail_request_identifier(name, context)
        return valid_identifier

    def parse_string_name(self, expression: StrExpr) -> str | None:
        name = expression.value
        if self._check_valid_identifier(name, expression):
            return name
        return None

    def parse_name_from_type(self, type_: Type, context: Context) -> str | None:
        if isinstance(type_, LiteralType) and isinstance(type_.value, str):
            name = type_.value
            if self._check_valid_identifier(name, context):
                return name
        else:
            self._fail_unreadable_identifier(context)
        return None

    def parse_name_from_expression(self, expression: Expression) -> str | None:
        type_ = self.checker.lookup_type_or_none(expression)
        if type_ is None:
            raise DeferralError(DeferralReason.REQUIRED_WAIT)
        return self.parse_name_from_type(type_, context=expression)

    def parse_name(self, expression: Expression) -> str | None:
        if isinstance(expression, StrExpr):
            return self.parse_string_name(expression)
        return self.parse_name_from_expression(expression)

    @abc.abstractmethod
    def _fail_invalid_identifier(self, name: str, context: Context) -> None: ...

    @abc.abstractmethod
    def _fail_keyword_identifier(self, name: str, context: Context) -> None: ...

    @abc.abstractmethod
    def _fail_request_identifier(self, name: str, context: Context) -> None: ...

    @abc.abstractmethod
    def _fail_unreadable_identifier(self, context: Context) -> None: ...
