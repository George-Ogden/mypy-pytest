from dataclasses import dataclass

from mypy.checker import TypeChecker
from mypy.subtypes import is_same_type

from .checker_wrapper import CheckerWrapper
from .fullname import Fullname
from .test_utils import parse_multiple


@dataclass
class CheckerWrapperMock(CheckerWrapper):
    checker: TypeChecker


def _lookup_fullname_type_test_body(sources: list[tuple[str, str]], fullname: str) -> None:
    parse_result = parse_multiple(sources)
    [*_, (last_module_name, _)] = sources
    checker = parse_result.checkers[last_module_name]
    expected_type = parse_result.types[last_module_name].get("expected")
    checker_wrapper = CheckerWrapperMock(checker)
    if expected_type is None:
        assert checker_wrapper.lookup_fullname_type(Fullname.from_string(fullname)) is None
    else:
        type_ = checker_wrapper.lookup_fullname_type(Fullname.from_string(fullname))
        assert type_ is not None
        assert is_same_type(type_, expected_type)


def test_lookup_fullname_one_flat_module_exists() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                x: int
                expected: int
                """,
            )
        ],
        "test_module.x",
    )


def test_lookup_fullname_one_flat_module_does_not_exist() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                x: int
                """,
            )
        ],
        "test_module.y",
    )


def test_lookup_fullname_many_flat_modules_exists() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                x: str
                """,
            ),
            (
                "test_module.nested",
                """
                x: int
                expected: int
                """,
            ),
        ],
        "test_module.nested.x",
    )


def test_lookup_fullname_many_nested_modules_exists() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                class x:
                    x: int
                """,
            ),
            (
                "test_module.x",
                """
                y: str
                expected: int
                """,
            ),
        ],
        "test_module.x.x",
    )


def test_lookup_fullname_many_nested_modules_conflicting() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                class x:
                    x: int
                """,
            ),
            (
                "test_module.x",
                """
                x: str
                expected: int
                """,
            ),
        ],
        "test_module.x.x",
    )


def test_lookup_fullname_many_nested_modules_with_import() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                from .x import x as y
                class x:
                    x: int
                """,
            ),
            (
                "test_module.x",
                """
                from typing import Any

                x: str
                expected: Any # import detected but not fully analyzed
                """,
            ),
        ],
        "test_module.y",
    )


def test_lookup_fullname_many_nested_modules_does_not_exist() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                """
                from .x import x as y
                class x:
                    x: int
                """,
            ),
            (
                "test_module.x",
                """
                x: str
                """,
            ),
        ],
        "test_module.doesnotexist",
    )


def test_lookup_fullname_many_nested_modules_exists_as_module() -> None:
    _lookup_fullname_type_test_body(
        [
            (
                "test_module",
                "",
            ),
            (
                "test_module.x",
                "",
            ),
        ],
        "test_module.x",
    )
