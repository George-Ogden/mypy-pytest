from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.expandtype import expand_type_by_instance
from mypy.nodes import CallExpr, Expression, StrExpr
from mypy.types import CallableType, Instance, LiteralType, Overloaded, Parameters, Type, UnionType

from .argmapper import ArgMapper
from .checker_wrapper import CheckerWrapper
from .fullname import Fullname
from .types_module import TYPES_MODULE


@dataclass(frozen=True, slots=True)
class PatchCallChecker(CheckerWrapper):
    checker: TypeChecker

    def add_patch_generics(self, call: CallExpr) -> Type | None:
        if (
            (target_arg := self._target_arg(call)) is not None
            and (arg_value := self._string_value(target_arg)) is not None
            and (
                original_type := self.lookup_fullname_type(
                    Fullname.from_string(arg_value), context=target_arg
                )
            )
        ):
            return self._specialized_patcher_type(original_type)
        return None

    def _target_arg(self, call: CallExpr) -> Expression | None:
        return ArgMapper.named_arg_mapping(call, self.checker).get("target")

    def _string_value(self, expression: Expression) -> str | None:
        if isinstance(expression, StrExpr):
            return expression.value
        if isinstance(
            literal_type := self.checker.lookup_type(expression), LiteralType
        ) and isinstance(literal_type.value, str):
            return literal_type.value
        return None

    def _specialized_patcher_type(
        self, original_type: Type, *, attribute: str | None = None
    ) -> Type | None:
        if (mock_bound := self._mock_bound(original_type)) is None:
            return None
        instance_type = self.checker.named_generic_type(
            f"{TYPES_MODULE}.mock._patcher", [mock_bound]
        )
        if attribute is None:
            return instance_type
        return self._specialized_patcher_attribute_type(instance_type, attribute)

    @classmethod
    def _specialized_patcher_attribute_type(
        cls, instance_type: Instance, attribute: str
    ) -> Type | None:
        attribute_type = instance_type.type.names[attribute].type
        if attribute_type is None:
            return attribute_type
        return expand_type_by_instance(attribute_type, instance_type)

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
        if isinstance(original_type, Instance):
            return UnionType(
                [self.checker.named_type(f"{TYPES_MODULE}.mock.MagicMock"), original_type]
            )
        return None
