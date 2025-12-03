from collections.abc import Sequence
from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.nodes import CallExpr, Expression, ListExpr, SetExpr, TupleExpr
from mypy.subtypes import is_subtype
from mypy.types import Type

from .checker_wrapper import CheckerWrapper
from .error_codes import PARAM_USEFIXTURES
from .fullname import Fullname


@dataclass(frozen=True, slots=True)
class ParamMarkChecker(CheckerWrapper):
    checker: TypeChecker

    def check_param_marks(self, param: CallExpr) -> None:
        mark_arg = self._named_mark_arg(param)
        if mark_arg is not None:
            self.check_mark_arg(mark_arg)

    def _named_mark_arg(self, call: CallExpr) -> Expression | None:
        for arg, arg_name in zip(call.args, call.arg_names, strict=True):
            if arg_name == "marks":
                return arg
        return None

    def check_mark_arg(self, arg: Expression) -> None:
        match self._arg_marks(arg):
            case list() as marks:
                self.check_marks(marks)
            case mark:
                self.check_mark(mark)

    def _arg_marks(self, arg: Expression) -> list[Expression] | Expression:
        if isinstance(arg, ListExpr | TupleExpr | SetExpr):
            return arg.items
        return arg

    def check_marks(self, marks: Sequence[Expression]) -> None:
        for mark in marks:
            self.check_mark(mark)

    def check_mark(self, mark: Expression) -> None:
        if isinstance(mark, CallExpr) and is_subtype(
            self.checker.lookup_type(mark.callee), self.single_type
        ):
            self.checker.fail(
                "`pytest.mark.usefixtures` is not allowed in a `pytest.param`.",
                context=mark,
                code=PARAM_USEFIXTURES,
            )

    @property
    def single_type(self) -> Type:
        return self.named_type(
            Fullname.from_string("_pytest.mark.structures._UsefixturesMarkDecorator")
        )
