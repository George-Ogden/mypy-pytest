from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Context, Expression, MemberExpr
from mypy.types import AnyType, Type

from .argmapper import ArgMapper
from .patch_call_checker import PatchCallChecker


@dataclass(frozen=True, slots=True)
class ObjectPatchCallChecker(PatchCallChecker):
    checker: TypeChecker

    def add_patch_generics(self, call: CallExpr) -> Type | None:
        if (
            (target_arg := self._target_arg(call)) is not None
            and (attribute_arg := self._attribute_arg(call)) is not None
            and (attribute_value := self._string_value(attribute_arg)) is not None
            and (
                original_type := self._attribute_type(
                    target_arg, attribute_value, context=attribute_arg
                )
            )
            is not None
        ):
            return self._specialized_patcher_type(original_type, attribute="object")
        return None

    def _attribute_arg(self, call: CallExpr) -> Expression | None:
        return ArgMapper.named_arg_mapping(call, self.checker).get("attribute")

    def _attribute_type(self, base: Expression, attribute: str, *, context: Context) -> Type | None:
        member = MemberExpr(base, name=attribute)
        member.line = context.line
        member.column = context.column
        type_ = self.checker.expr_checker.analyze_ordinary_member_access(member, is_lvalue=False)
        if isinstance(type_, AnyType) and type_.is_from_error:
            return None
        return type_
