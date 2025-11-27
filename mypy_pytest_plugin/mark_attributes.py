from dataclasses import dataclass
import functools

from mypy.checker import TypeChecker

from .pytest_config_manager import PytestConfigManager


@dataclass(frozen=True)
class MarkChecker:
    checker: TypeChecker

    def is_valid_mark(self, name: str) -> bool:
        return not name.startswith("_") and (
            name in self.predefined_names or name in self.user_defined_names
        )

    @functools.cached_property
    def predefined_names(self) -> set[str]:
        return set(self.checker.named_type("pytest.MarkGenerator").type.names)

    @functools.cached_property
    def user_defined_names(self) -> set[str]:
        return {line.split(":")[0].split("(")[0].strip() for line in PytestConfigManager.markers()}
