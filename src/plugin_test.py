from .plugin import PytestPlugin


def _fn_name_test_body(fullname: str, expected: bool) -> None:
    assert PytestPlugin.is_test_fn_name(fullname) == expected


def test_is_test_fn_all_valid() -> None:
    _fn_name_test_body("file_test.test_fn", True)


def test_is_test_fn_nested_valid() -> None:
    _fn_name_test_body("src.foo_test.test_bar", True)


def test_is_test_fn_fn_name_invalid() -> None:
    _fn_name_test_body("file_test.utility_method", False)


def test_is_test_fn_file_name_invalid() -> None:
    _fn_name_test_body("file.test_fn", False)
