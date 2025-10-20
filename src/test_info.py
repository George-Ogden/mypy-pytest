from dataclasses import dataclass
from typing import cast

from mypy.checker import TypeChecker
from mypy.nodes import Expression, ListExpr, StrExpr, TupleExpr

from .error_codes import INVALID_ARGNAME, UNREADABLE_ARGNAME


@dataclass(frozen=True, slots=True, kw_only=True)
class TestInfo:
    checker: TypeChecker

    def _check_valid_identifier(self, name: str, context: StrExpr) -> bool:
        if name.isidentifier():
            return True
        self.checker.msg.fail(
            f"Invalid identifier {name!r}.", context=context, code=INVALID_ARGNAME
        )
        return False

    def parse_names_string(self, node: StrExpr) -> list[str] | None:
        individual_names = [name.strip() for name in node.value.split(",")]
        filtered_names = [name for name in individual_names if name]
        if any([not self._check_valid_identifier(name, node) for name in filtered_names]):
            return None
        return filtered_names

    def _parse_name(self, node: Expression) -> str | None:
        if isinstance(node, StrExpr):
            name = node.value
            if self._check_valid_identifier(name, node):
                return name
        else:
            self.checker.msg.fail(
                "Unable to read identifier. (Use a sequence of strings instead.)",
                context=node,
                code=UNREADABLE_ARGNAME,
            )
        return None

    def parse_names_sequence(self, node: TupleExpr | ListExpr) -> list[str] | None:
        names = [self._parse_name(item) for item in node.items]
        if all([isinstance(name, str) for name in names]):
            return cast(list[str], names)
        return None
