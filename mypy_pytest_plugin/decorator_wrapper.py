from collections.abc import Sequence
from dataclasses import dataclass
from typing import Self, TypeGuard

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Expression
from mypy.types import Instance

from .argmapper import ArgMapper
from .error_codes import UNREADABLE_ARGNAMES_ARGVALUES


@dataclass(frozen=True, slots=True)
class DecoratorWrapper:
    call: CallExpr
    checker: TypeChecker

    @classmethod
    def decorators_from_nodes(
        cls, nodes: Sequence[Expression], *, checker: TypeChecker
    ) -> Sequence[Self]:
        return [
            cls(node, checker=checker)
            for node in nodes
            if cls._is_parametrized_decorator_node(node, checker=checker)
        ]

    @classmethod
    def _is_parametrized_decorator_node(
        cls, node: Expression, checker: TypeChecker
    ) -> TypeGuard[CallExpr]:
        if isinstance(node, CallExpr):
            callee_type = node.callee.accept(checker.expr_checker)
            return (
                isinstance(callee_type, Instance)
                and callee_type.type.fullname == "_pytest.mark.structures._ParametrizeMarkDecorator"
            )
        return False

    @property
    def arg_names_and_arg_values(self) -> tuple[Expression, Expression] | None:
        name_mapping = ArgMapper.named_arg_mapping(self.call, self.checker)
        try:
            return name_mapping["argnames"], name_mapping["argvalues"]
        except KeyError:
            self.checker.fail(
                "Unable to read argnames and argvalues. Use positional or keyword arguments.",
                context=self.call,
                code=UNREADABLE_ARGNAMES_ARGVALUES,
            )
            return None
