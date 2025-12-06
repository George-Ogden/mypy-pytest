from collections.abc import Collection
import functools
from typing import Final

from mypy.argmap import map_formals_to_actuals
from mypy.checker import TypeChecker
from mypy.nodes import ArgKind, CallExpr, Expression
from mypy.typeops import bind_self
from mypy.types import CallableType, FunctionLike, Instance, Overloaded, Type

type ArgMap = dict[str, Expression]


class ArgMapper:
    ACCEPTED_ARG_KINDS: Final[Collection[ArgKind]] = (ArgKind.ARG_POS, ArgKind.ARG_NAMED)

    @classmethod
    def named_arg_mapping(cls, call: CallExpr, checker: TypeChecker) -> ArgMap:
        callee_type = checker.lookup_type(call.callee)
        return cls._named_arg_type_mapping(call, callee_type, checker)

    @classmethod
    def _named_arg_type_mapping(
        cls, call: CallExpr, callee_type: Type, checker: TypeChecker
    ) -> ArgMap:
        if isinstance(callee_type, CallableType):
            return cls._named_arg_callable_mapping(call, callee_type, checker)
        if isinstance(callee_type, Overloaded):
            return cls._named_arg_overloaded_mapping(call, callee_type, checker)
        if (
            isinstance(callee_type, Instance)
            and (call_node := callee_type.type.names.get("__call__")) is not None
            and call_node.type is not None
        ):
            type_ = call_node.type
            if isinstance(type_, FunctionLike):
                type_ = bind_self(type_, callee_type)
                return cls._named_arg_type_mapping(call, type_, checker)
        return {}

    @classmethod
    def _named_arg_callable_mapping(
        cls, call: CallExpr, callee_type: CallableType, checker: TypeChecker
    ) -> ArgMap:
        mapping = map_formals_to_actuals(
            actual_kinds=call.arg_kinds,
            actual_names=call.arg_names,
            formal_kinds=callee_type.arg_kinds,
            formal_names=callee_type.arg_names,
            actual_arg_type=lambda i: call.args[i].accept(checker.expr_checker),
        )

        return {
            arg_name: call.args[actual_idx]
            for actual_idx, formal_idxs in enumerate(mapping)
            if len(formal_idxs) == 1
            and callee_type.arg_kinds[formal_idx := formal_idxs[0]] in cls.ACCEPTED_ARG_KINDS
            and formal_idx < len(callee_type.arg_names)
            and (arg_name := callee_type.arg_names[formal_idx]) is not None
        }

    @classmethod
    def _named_arg_overloaded_mapping(
        cls, call: CallExpr, callee_type: Overloaded, checker: TypeChecker
    ) -> ArgMap:
        return functools.reduce(
            cls._merge_mappings,
            (
                cls._named_arg_callable_mapping(call, callable_type, checker)
                for callable_type in callee_type.items
            ),
        )

    @classmethod
    def _merge_mappings(cls, this: ArgMap, that: ArgMap) -> ArgMap:
        return {key: expr for key, expr in this.items() if that.get(key, None) is expr}

    @classmethod
    def named_arg(cls, call: CallExpr, name: str) -> Expression | None:
        expressions = [
            arg for arg_name, arg in zip(call.arg_names, call.args, strict=True) if arg_name == name
        ]
        match expressions:
            case [expression]:
                return expression
        return None
