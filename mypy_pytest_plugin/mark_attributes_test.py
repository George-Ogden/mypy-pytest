from .mark_attributes import MarkChecker
from .test_utils import parse


def _mark_name_test_body(name: str, valid: bool) -> None:
    pytest_source_mock = """
    from typing import Any

    class MarkGenerator:
        skip: Any
        parametrize: Any
        def __getattr__(self, name: str) -> Any:
            raise NotImplementedError()
        def _config(self) -> None: ...
    """
    parse_result = parse(pytest_source_mock, module_name="pytest")
    parse_result.accept_all()

    mark_checker = MarkChecker(parse_result.checker)
    assert mark_checker.is_valid_mark(name) == valid


def test_mark_name_starts_with_underscore() -> None:
    _mark_name_test_body("_parametrize", False)


def test_mark_name_valid() -> None:
    _mark_name_test_body("parametrize", True)


def test_mark_name_not_predefined() -> None:
    _mark_name_test_body("invalid", False)


def test_mark_name_user_defined() -> None:
    _mark_name_test_body("used_for_testing", True)
