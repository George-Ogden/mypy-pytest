class MarkChecker:
    def is_valid_mark(self, name: str) -> bool:
        return not name.startswith("_")
