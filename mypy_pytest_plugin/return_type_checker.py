from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.messages import format_type
from mypy.nodes import FuncDef
from mypy.options import Options
from mypy.types import AnyType, CallableType, NoneType, Type, TypeOfAny

from .checker_wrapper import CheckerWrapper
from .error_codes import TEST_RETURN_TYPE


@dataclass(frozen=True, eq=False)
class ReturnTypeChecker(CheckerWrapper):
    checker: TypeChecker

    @classmethod
    def check_return_type(cls, fn: FuncDef, *, checker: TypeChecker) -> None:
        cls(checker).check(fn)

    @property
    def options(self) -> Options:
        return self.checker.options

    def check(self, fn: FuncDef) -> None:
        if isinstance(fn_type := fn.type, CallableType) and not (
            self.is_valid_return_type(ret_type := fn_type.ret_type)
        ):
            self.fail(
                f"Test definitions must return {format_type(NoneType(), self.options)}, got {format_type(ret_type, self.options)}.",
                context=ret_type,
                code=TEST_RETURN_TYPE,
            )

    def is_valid_return_type(self, type_: Type) -> bool:
        return isinstance(type_, NoneType) or (
            isinstance(type_, AnyType) and type_.type_of_any == TypeOfAny.unannotated
        )
