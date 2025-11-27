from dataclasses import dataclass
import functools

from mypy.checker import TypeChecker


@dataclass(frozen=True)
class MarkChecker:
    checker: TypeChecker

    def is_valid_mark(self, name: str) -> bool:
        return not name.startswith("_") and name in self.predefined_names

    @functools.cached_property
    def predefined_names(self) -> set[str]:
        return set(self.checker.named_type("pytest.MarkGenerator").type.names)
