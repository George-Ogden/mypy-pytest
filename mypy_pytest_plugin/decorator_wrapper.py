from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Self, TypeGuard

from mypy.argmap import map_actuals_to_formals
from mypy.checker import TypeChecker
from mypy.nodes import ArgKind, CallExpr, Expression
from mypy.types import CallableType, Instance, Type

from .error_codes import VARIADIC_ARGNAMES_ARGVALUES
from .error_info import ExtendedContext
from .logger import Logger


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

    def _get_arg_type(self, i: int) -> Type:
        # subtract one for self
        i -= 1
        return self.call.args[i].accept(self.checker.expr_checker)

    @property
    def arg_names_and_arg_values(self) -> tuple[Expression, Expression] | None:
        mapping = map_actuals_to_formals(
            actual_kinds=[ArgKind.ARG_POS, *self.call.arg_kinds],
            actual_names=[None, *self.call.arg_names],
            formal_kinds=self.fn_type.arg_kinds,
            formal_names=self.fn_type.arg_names,
            actual_arg_type=self._get_arg_type,
        )
        return self._check_actuals_formals_mapping(mapping)

    @property
    def fn_type(self) -> CallableType:
        callee_type = self.call.callee.accept(self.checker.expr_checker)
        assert isinstance(callee_type, Instance)
        fn_type = callee_type.type.names["__call__"].type
        assert isinstance(fn_type, CallableType)
        return fn_type

    def _check_actuals_formals_mapping(
        self, mapping: list[list[int]]
    ) -> tuple[Expression, Expression] | None:
        arg_names_idx, arg_values_idx, *_ = self._clean_up_actuals_formals_mapping(mapping)
        if (
            self.call.arg_kinds[arg_values_idx] in self.accepted_arg_kinds
            and self.call.arg_kinds[arg_names_idx] in self.accepted_arg_kinds
        ):
            return self.call.args[arg_names_idx], self.call.args[arg_values_idx]
        Logger.error(
            "Unable to read argnames and argvalues in a variadic argument.",
            context=ExtendedContext.from_context(self.call, self.checker),
            code=VARIADIC_ARGNAMES_ARGVALUES,
        )
        return None

    def _clean_up_actuals_formals_mapping(
        self, mapping: list[list[int]]
    ) -> tuple[int, int, list[list[int]]]:
        [_, [arg_names_idx], [arg_values_idx], *extras] = mapping
        arg_values_idx -= 1
        arg_names_idx -= 1
        return arg_names_idx, arg_values_idx, extras

    @property
    def accepted_arg_kinds(self) -> Collection[ArgKind]:
        return (ArgKind.ARG_POS, ArgKind.ARG_NAMED)
