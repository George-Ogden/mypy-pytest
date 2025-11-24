import abc
from dataclasses import dataclass
import re

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Expression, SymbolTableNode, TypeInfo
from mypy.plugin import (
    FunctionContext,
    MethodContext,
)
from mypy.typeops import bind_self, type_object_type
from mypy.types import (
    FunctionLike,
    Instance,
    Type,
)

from .object_patch_call_checker import ObjectPatchCallChecker
from .patch_call_checker import PatchCallChecker
from .types_module import TYPES_MODULE


@dataclass(frozen=True, slots=True)
class MockCallChecker[T: MethodContext | FunctionContext](abc.ABC):
    checker: TypeChecker

    @classmethod
    def check_mock_calls(cls, ctx: T, *, fullname: str) -> Type:
        if isinstance(ctx.api, TypeChecker) and isinstance(ctx.context, CallExpr):
            mock_call_checker = cls(ctx.api)
            updated_callee_type = mock_call_checker.update_callee_type(ctx.context, fullname)
            if updated_callee_type is not None:
                return mock_call_checker.check_call(ctx.context, updated_callee_type)
        return ctx.default_return_type

    def update_callee_type(self, call: CallExpr, fullname: str) -> Type | None:
        if fullname == "unittest.mock._patcher.__call__":
            return PatchCallChecker(self.checker).add_patch_generics(call)
        if fullname == "unittest.mock._patcher.object":
            return ObjectPatchCallChecker(self.checker).add_patch_generics(call)
        return self.inject_mock_stub(call.callee, fullname)

    def check_call(self, call: CallExpr, callee_type: Type) -> Type:
        result_type, _inferred_type = self.checker.expr_checker.check_call(
            callee=callee_type,
            args=call.args,
            arg_kinds=call.arg_kinds,
            context=call,
            arg_names=call.arg_names,
        )
        return result_type

    def inject_mock_stub(
        self,
        callee: Expression,
        fullname: str,
    ) -> Type | None:
        fullname = re.sub(r"^unittest", TYPES_MODULE, fullname, count=1)
        if (
            symbol_table_node := self._lookup_symbol_table_node(fullname)
        ) is None or symbol_table_node.fullname != fullname:
            return None
        callee_type = self._get_type_from_symbol_table(symbol_table_node)

        original_callee_type = self.checker.lookup_type(callee)
        if isinstance(original_callee_type, Instance) and isinstance(callee_type, FunctionLike):
            callee_type = bind_self(callee_type, original_callee_type)

        return callee_type

    def _get_type_from_symbol_table(self, node: SymbolTableNode) -> Type | None:
        if isinstance(node.node, TypeInfo):
            type_info = node.node
            return type_object_type(type_info, self.checker.named_type)
        return node.type

    @abc.abstractmethod
    def _lookup_symbol_table_node(self, fullname: str) -> SymbolTableNode | None: ...


@dataclass(frozen=True, slots=True)
class FunctionMockCallChecker(MockCallChecker[FunctionContext]):
    def _lookup_symbol_table_node(self, fullname: str) -> SymbolTableNode | None:
        try:
            return self.checker.lookup_qualified(fullname)
        except KeyError:
            return None


@dataclass(frozen=True, slots=True)
class MethodMockCallChecker(MockCallChecker[MethodContext]):
    def _lookup_symbol_table_node(self, fullname: str) -> SymbolTableNode | None:
        class_fullname, name = fullname.rsplit(".", maxsplit=1)
        try:
            class_symbol_table_node = self.checker.lookup_qualified(class_fullname)
            assert isinstance(class_symbol_table_node.node, TypeInfo)
            return class_symbol_table_node.node.names[name]
        except KeyError:
            return None
