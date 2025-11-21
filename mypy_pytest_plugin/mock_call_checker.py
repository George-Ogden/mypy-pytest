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

from .types_module import TYPES_MODULE


@dataclass(frozen=True, slots=True)
class MockCallChecker[T: MethodContext | FunctionContext](abc.ABC):
    checker: TypeChecker

    @classmethod
    def check_mock_calls(cls, ctx: T, *, fullname: str) -> Type:
        if isinstance(ctx.api, TypeChecker) and isinstance(ctx.context, CallExpr):
            updated_call_type = cls(ctx.api).update_call_type(ctx.context, fullname)
            if updated_call_type is not None:
                return updated_call_type
        return ctx.default_return_type

    def update_call_type(self, call: CallExpr, fullname: str) -> Type | None:
        if (callee_type := self.inject_mock_stub(call.callee, fullname)) is None:
            return None
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
        callee_type = self._get_type_from_symbol_table(self._lookup_symbol_table_node(fullname))

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
    def _lookup_symbol_table_node(self, fullname: str) -> SymbolTableNode: ...


@dataclass(frozen=True, slots=True)
class FunctionMockCallChecker(MockCallChecker[FunctionContext]):
    def _lookup_symbol_table_node(self, fullname: str) -> SymbolTableNode:
        return self.checker.lookup_qualified(fullname)


@dataclass(frozen=True, slots=True)
class MethodMockCallChecker(MockCallChecker[MethodContext]):
    def _lookup_symbol_table_node(self, fullname: str) -> SymbolTableNode:
        class_fullname, name = fullname.rsplit(".", maxsplit=1)
        class_symbol_table_node = self.checker.lookup_qualified(class_fullname)
        assert isinstance(class_symbol_table_node.node, TypeInfo)
        return class_symbol_table_node.node.names[name]
