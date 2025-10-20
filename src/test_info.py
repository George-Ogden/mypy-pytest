from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.nodes import StrExpr

from .error_codes import INVALID_ARGNAME


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
        if any(not self._check_valid_identifier(name, node) for name in filtered_names):
            return None
        return filtered_names
