from collections.abc import Collection, Sequence
from dataclasses import dataclass

from mypy.argmap import map_formals_to_actuals
from mypy.checker import TypeChecker
from mypy.messages import format_type
from mypy.nodes import ArgKind, CallExpr, Expression
from mypy.subtypes import is_subtype
from mypy.types import CallableType, Instance, Type

from .error_codes import ITERABLE_SEQUENCE


@dataclass(frozen=True, slots=True)
class IterableSequenceChecker:
    checker: TypeChecker

    def check_iterable_sequence_call(self, call: CallExpr) -> None:
        for argument, expected_type in self.actuals_formals_mapping_bijective_subset(call):
            argument_type = self.checker.lookup_type(argument)
            if self.is_sequence(argument_type) and self.is_iterable(expected_type):
                self._display_error_message(expected_type, argument_type, argument)

    def _display_error_message(
        self, expected_type: Type, argument_type: Type, context: Expression
    ) -> None:
        self.checker.fail(
            f"Expected {format_type(expected_type, self.checker.options)}, got {format_type(argument_type, self.checker.options)}.",
            context,
            code=ITERABLE_SEQUENCE,
        )
        self.checker.note(
            "This still type checks, but could be made more robust by using `iter()`",
            context,
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
