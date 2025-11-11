from .plugin import PytestPlugin
from .test_utils import parse


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


def test_register_ignored_fns() -> None:
    parse_result = parse(
        f"""
        from {PytestPlugin.TYPES_MODULE} import Testable
        from typing import Literal

        @Testable
        def test_1() -> None: ...

        @Testable
        def test_2() -> None: ...

        @Testable
        def test_3() -> None: ...

        @Testable
        def test_4() -> None: ...

        @Testable
        def test_5() -> None: ...

        @Testable
        def test_6() -> None: ...

        test_1.__test__ = False

        f: Literal[False] = False

        test_3.__test__ = f

        b: bool = False

        test_4.__test__ = b

        test_5.__test__ = test_6.__test__ = False
        """
    )

    for statement in parse_result.raw_defs:
        statement.accept(parse_result.checker)
    ignored_tests = PytestPlugin._ignored_test_names_from_statements(
        parse_result.raw_defs, parse_result.checker
    )
    assert ignored_tests == {"test_1", "test_3", "test_5", "test_6"}
