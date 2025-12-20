from mypy.nodes import FuncDef

from .return_type_checker import ReturnTypeChecker
from .test_utils import check_error_messages, get_error_messages, parse


def _return_type_check_test_body(defs: str, *, passes: bool) -> None:
    parse_result = parse(defs)

    return_test = parse_result.defs["return_test"]
    assert isinstance(return_test, FuncDef)

    checker = parse_result.checker

    ReturnTypeChecker.check_return_type(return_test, checker=checker)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=None if passes else ["test-return-type"])


def test_return_type_check_explicit_return_none() -> None:
    _return_type_check_test_body(
        """
        def return_test() -> None:
            ...
        """,
        passes=True,
    )


def test_return_type_check_explicit_return_any() -> None:
    _return_type_check_test_body(
        """
        from typing import Any

        def return_test() -> Any:
            ...
        """,
        passes=False,
    )


def test_return_type_check_generates_none() -> None:
    _return_type_check_test_body(
        """
        from typing import Generator

        def return_test() -> Generator[None]:
            yield None
        """,
        passes=False,
    )


def test_return_type_check_returns_non_none_no_annotations() -> None:
    _return_type_check_test_body(
        """
        def return_test():
            return 2
        """,
        passes=True,
    )


def test_return_type_check_returns_non_none_partial_annotation() -> None:
    _return_type_check_test_body(
        """
        def return_test(x: int):
            return x
        """,
        passes=True,
    )
