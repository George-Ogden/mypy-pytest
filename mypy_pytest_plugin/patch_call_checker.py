from dataclasses import dataclass
from typing import Any

from mypy.checker import TypeChecker
from mypy.nodes import (
    ArgKind,
    CallExpr,
    Expression,
    MypyFile,
    StrExpr,
)
from mypy.types import (
    CallableType,
    Instance,
    LiteralType,
    Overloaded,
    Parameters,
    Type,
    UnionType,
)

from .fullname import Fullname
from .types_module import TYPES_MODULE


@dataclass(frozen=True, slots=True)
class PatchCallChecker:
    checker: TypeChecker

    def add_patch_generics(self, call: CallExpr) -> Type | None:
        if (
            (target_arg := self._target_arg(call)) is not None
            and (arg_value := self._string_value(target_arg)) is not None
            and (original_type := self._lookup_fullname_type(arg_value))
        ):
            return self._specialized_patcher_type(original_type)
        return None

    @classmethod
    def _target_arg(cls, call: CallExpr) -> Expression | None:
        if len(call.args) > 0:
            if call.arg_names[0] is None and call.arg_kinds[0] == ArgKind.ARG_POS:
                return call.args[0]
            try:
                index = call.arg_names.index("target")
            except ValueError:
                ...
            else:
                if call.arg_kinds[1] == ArgKind.ARG_NAMED:
                    return call.args[index]
        return None

    def _string_value(self, expression: Expression) -> str | None:
        if isinstance(expression, StrExpr):
            return expression.value
        if isinstance(
            literal_type := self.checker.lookup_type(expression), LiteralType
        ) and isinstance(literal_type.value, str):
            return literal_type.value
        return None

    def _lookup_fullname_type(self, fullname: str) -> Type | None:
        module_name, target = Fullname.from_string(fullname), Fullname(())
        while module_name:
            if (module := self.checker.modules.get(str(module_name))) and (
                type_ := self._lookup_fullname_type_in_module(module, target)
            ):
                return type_
            target = target.push_front(module_name.name)
            module_name = module_name.module_name
        return None

    def _lookup_fullname_type_in_module(self, module: MypyFile, target: Fullname) -> Type | None:
        resource: Any = module
        for name in target:
            try:
                resource = resource.names[name].node
            except KeyError:
                return None
        try:
            return resource.type
        except AttributeError:
            return None

    def _specialized_patcher_type(self, original_type: Type) -> Instance | None:
        if (mock_bound := self._mock_bound(original_type)) is None:
            return None
        return self.checker.named_generic_type(f"{TYPES_MODULE}.mock._patcher", [mock_bound])

    def _mock_bound(self, original_type: Type) -> Type | None:
        if isinstance(original_type, CallableType):
            parameters = Parameters(
                original_type.arg_types,
                original_type.arg_kinds,
                original_type.arg_names,
                variables=original_type.variables,
                is_ellipsis_args=original_type.is_ellipsis_args,
                imprecise_arg_kinds=original_type.imprecise_arg_kinds,
            )
            ret = original_type.ret_type
            return UnionType(
                [
                    self.checker.named_generic_type(f"{TYPES_MODULE}.mock.Mock", [parameters, ret]),
                    original_type,
                ]
            )
        if isinstance(original_type, Overloaded):
            return original_type
        return None
