import re

from mypy.nodes import StrExpr

from .test_info import TestInfo
from .test_utils import parse_defs, parse_types


def _test_info_parse_names_string_test_body(
    source: str, names: list[str] | None, *, errors: list[str] | None = None
) -> None:
    type_checker, _ = parse_types("")
    test_info = TestInfo(checker=type_checker)

    source = f"names = {source}"
    node_mapping = parse_defs(source)
    names_node = node_mapping["names"]
    assert isinstance(names_node, StrExpr)

    assert not type_checker.errors.is_errors()
    assert test_info.parse_names_string(names_node) == names
    messages = "\n".join(type_checker.errors.new_messages())
    if errors:
        error_codes = [match for match in re.findall(r"\[([a-z\-]*)\]", messages)]
        assert error_codes == errors, messages
    else:
        assert not type_checker.errors.is_errors()


def test_test_info_parse_names_string_empty() -> None:
    _test_info_parse_names_string_test_body("''", [])


def test_test_info_parse_names_string_noise_only() -> None:
    _test_info_parse_names_string_test_body("',, , , ,  '", [])


def test_test_info_parse_names_string_one_item() -> None:
    _test_info_parse_names_string_test_body("'bar'", ["bar"])


def test_test_info_parse_names_string_one_item_extra_noise() -> None:
    _test_info_parse_names_string_test_body("', foo_8,,, , '", ["foo_8"])


def test_test_info_parse_names_string_three_items() -> None:
    _test_info_parse_names_string_test_body("'a, b_, __c'", ["a", "b_", "__c"])


def test_test_info_parse_names_string_two_items_extra_noise() -> None:
    _test_info_parse_names_string_test_body("',  aa ,b,b,    ,,,,,,,,d  '", ["aa", "b", "b", "d"])


def test_info_parse_names_string_starting_with_number() -> None:
    _test_info_parse_names_string_test_body("'8ac'", None, errors=["invalid-argname"])


def test_test_info_parse_names_string_with_space() -> None:
    _test_info_parse_names_string_test_body("'aa b'", None, errors=["invalid-argname"])
