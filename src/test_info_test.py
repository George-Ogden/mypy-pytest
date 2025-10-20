from .test_info import TestInfo


def _test_info_parse_names_string_test_body(string: str, names: list[str] | None) -> None:
    assert TestInfo.parse_names_string(string) == names


def test_test_info_parse_names_string_empty() -> None:
    _test_info_parse_names_string_test_body("", [])


def test_test_info_parse_names_string_noise_only() -> None:
    _test_info_parse_names_string_test_body(",, , , ,  ", [])


def test_test_info_parse_names_string_one_item() -> None:
    _test_info_parse_names_string_test_body("bar", ["bar"])


def test_test_info_parse_names_string_one_item_extra_noise() -> None:
    _test_info_parse_names_string_test_body(", foo_8,,, , ", ["foo_8"])


def test_test_info_parse_names_string_three_items() -> None:
    _test_info_parse_names_string_test_body("a, b_, __c", ["a", "b_", "__c"])


def test_test_info_parse_names_string_two_items_extra_noise() -> None:
    _test_info_parse_names_string_test_body(",  aa ,b,b,    ,,,,,,,,d  ", ["aa", "b", "b", "d"])


def test_info_parse_names_string_starting_with_number() -> None:
    _test_info_parse_names_string_test_body("8ac", None)


def test_test_info_parse_names_string_with_space() -> None:
    _test_info_parse_names_string_test_body("aa b", None)


def test_test_info_parse_names_string_with_invalid_name() -> None:
    _test_info_parse_names_string_test_body("aaa, b b, c", None)
