from .mark_attributes import MarkChecker


def _mark_name_test_body(name: str, valid: bool) -> None:
    mark_checker = MarkChecker()
    assert mark_checker.is_valid_mark(name) == valid


def test_mark_name_starts_with_underscore() -> None:
    _mark_name_test_body("_parametrize", False)


def test_mark_name_starts_without_underscore() -> None:
    _mark_name_test_body("parametrize", True)
