from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class TestInfo:
    @classmethod
    def parse_names_string(cls, string: str) -> list[str] | None:
        individual_names = [name.strip() for name in string.split(",")]
        filtered_names = [name for name in individual_names if name]
        if any(not name.isidentifier() for name in filtered_names):
            return None
        return filtered_names
