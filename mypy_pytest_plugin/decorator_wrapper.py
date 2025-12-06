from collections.abc import Sequence
from dataclasses import dataclass
import functools
from typing import Self, TypeGuard

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Expression
from mypy.types import Instance

from .argmapper import ArgMapper
from .checker_wrapper import CheckerWrapper
from .error_codes import UNREADABLE_ARGNAMES_ARGVALUES


@dataclass(frozen=True, slots=True)
class DecoratorWrapper(CheckerWrapper):
    call: CallExpr
    checker: TypeChecker

    @classmethod
    def decorators_from_exprs(
        cls, exprs: Sequence[Expression], *, checker: TypeChecker
    ) -> Sequence[Self]:
        return [
            cls(node, checker=checker)
            for node in exprs
            if cls._is_parametrized_decorator_expr(node, checker=checker)
        ]

    @classmethod
    def _is_parametrized_decorator_expr(
        cls, expr: Expression, checker: TypeChecker
    ) -> TypeGuard[CallExpr]:
        if isinstance(expr, CallExpr):
            callee_type = expr.callee.accept(checker.expr_checker)
            return (
                isinstance(callee_type, Instance)
                and callee_type.type.fullname == "_pytest.mark.structures._ParametrizeMarkDecorator"
            )
        return False

    @functools.cached_property
    def arg_names_and_arg_values(self) -> tuple[Expression, Expression] | None:
        name_mapping = ArgMapper.named_arg_mapping(self.call, self.checker)
        try:
            return name_mapping["argnames"], name_mapping["argvalues"]
        except KeyError:
            self.fail(
                "Unable to read argnames and argvalues. Use positional or keyword arguments.",
                context=self.call,
                code=UNREADABLE_ARGNAMES_ARGVALUES,
            )
            return None

    @property
    def arg_names(self) -> Expression | None:
        if self.arg_names_and_arg_values is None:
            return None
        arg_names, _arg_values = self.arg_names_and_arg_values
        return arg_names
