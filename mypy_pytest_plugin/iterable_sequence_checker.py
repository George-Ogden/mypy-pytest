from collections.abc import Collection, Sequence
from dataclasses import dataclass
import sys

from mypy.argmap import map_formals_to_actuals
from mypy.checker import TypeChecker
from mypy.messages import format_type
from mypy.nodes import ArgKind, CallExpr, Context, Expression
from mypy.subtypes import is_subtype
from mypy.types import CallableType, Instance, Type

from .checker_wrapper import CheckerWrapper
from .error_codes import ITERABLE_SEQUENCE


@dataclass(frozen=True, slots=True)
class IterableSequenceChecker(CheckerWrapper):
    checker: TypeChecker

    def check_iterable_sequence_call(self, call: CallExpr) -> None:
        if not self.is_builtin_function(call.callee):
            self.check_iterable_sequence_arguments(call)

    def is_builtin_function(self, expression: Expression) -> bool:
        expression_type = self.checker.lookup_type(expression)
        if (
            isinstance(expression_type, CallableType)
            and (def_ := expression_type.definition) is not None
        ):
            [module, *_] = def_.fullname.split(".", maxsplit=1) if def_ else [""]
            return module in sys.stdlib_module_names
        return False

    def check_iterable_sequence_arguments(self, call: CallExpr) -> None:
        for argument, expected_type in self.actuals_formals_mapping_bijective_subset(call):
            self.check_iterable_sequence_argument(argument, expected_type)

    def check_iterable_sequence_argument(self, argument: Expression, expected_type: Type) -> None:
        argument_type = self.checker.lookup_type(argument)
        if self.is_sequence(argument_type) and self.is_iterable(expected_type):
            self._display_error_message(expected_type, argument_type, argument)

    def _display_error_message(
        self, expected_type: Type, argument_type: Type, context: Context
    ) -> None:
        self.fail(
            f"Argument has type {format_type(argument_type, self.checker.options)}; expected {format_type(expected_type, self.checker.options)}.",
            context=context,
            code=ITERABLE_SEQUENCE,
        )
        self.note(
            "This still type checks, but could be made more robust by using `iter()`",
            context=context,
            code=ITERABLE_SEQUENCE,
        )

    def actuals_formals_mapping_bijective_subset(
        self, call: CallExpr
    ) -> Sequence[tuple[Expression, Type]]:
        callee_type = self.checker.lookup_type(call.callee)
        if not isinstance(callee_type, CallableType):
            return []

        mapping = map_formals_to_actuals(
            actual_kinds=call.arg_kinds,
            actual_names=call.arg_names,
            formal_kinds=callee_type.arg_kinds,
            formal_names=callee_type.arg_names,
            actual_arg_type=lambda i: call.args[i].accept(self.checker.expr_checker),
        )

        return [
            (call.args[actual_idx], callee_type.arg_types[formal_idxs[0]])
            for actual_idx, formal_idxs in enumerate(mapping)
            if call.arg_kinds[actual_idx] in self.accepted_arg_kinds and len(formal_idxs) == 1
        ]

    @property
    def accepted_arg_kinds(self) -> Collection[ArgKind]:
        return (ArgKind.ARG_POS, ArgKind.ARG_NAMED)

    def is_iterable(self, type_: Type) -> bool:
        return isinstance(type_, Instance) and type_.type.fullname == "typing.Iterable"

    def is_sequence(self, type_: Type) -> bool:
        return is_subtype(type_, self.checker.named_type("typing.Sequence"))
