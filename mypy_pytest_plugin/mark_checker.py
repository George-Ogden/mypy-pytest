from collections.abc import Sequence
from dataclasses import dataclass
import functools
import itertools

from mypy.checker import TypeChecker
from mypy.nodes import MemberExpr
from mypy.subtypes import is_same_type

from .error_codes import UNKNOWN_MARK
from .pytest_config_manager import PytestConfigManager


@dataclass(frozen=True)
class MarkChecker:
    checker: TypeChecker

    def check_attribute(self, expr: MemberExpr) -> None:
        if is_same_type(
            self.checker.lookup_type(expr.expr), self.checker.named_type("pytest.MarkGenerator")
        ) and not self.is_valid_mark(expr.name):
            error_msg = f"Invalid mark name {expr.name!r}."
            note_prefix = f"Expected a predefined mark (one of {self.predefined_names!r}) or "
            if self.user_defined_names:
                note_suffix = f"a user defined mark (one of {self.user_defined_names!r})."
            else:
                note_suffix = "see https://docs.pytest.org/en/stable/how-to/mark.html for how to register marks."
            self.checker.fail(error_msg, context=expr, code=UNKNOWN_MARK)
            self.checker.note(note_prefix + note_suffix, context=expr, code=UNKNOWN_MARK)

    def is_valid_mark(self, name: str) -> bool:
        return not name.startswith("_") and (name in self._mark_names_index)

    @functools.cached_property
    def _mark_names_index(self) -> set[str]:
        return set(itertools.chain(self.predefined_names, self.user_defined_names))

    @functools.cached_property
    def predefined_names(self) -> Sequence[str]:
        return [
            name
            for name in self.checker.named_type("pytest.MarkGenerator").type.names
            if not name.startswith("_")
        ]

    @functools.cached_property
    def user_defined_names(self) -> list[str]:
        return [
            name
            for line in PytestConfigManager.markers()
            if (name := line.split(":")[0].split("(")[0].strip()) and not name.startswith("_")
        ]
