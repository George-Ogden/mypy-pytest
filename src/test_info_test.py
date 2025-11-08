from typing import Callable, cast

from mypy.nodes import Expression, FuncDef

from .test_info import TestInfo
from .test_utils import (
    check_error_messages,
    default_test_info,
    default_type_checker,
    get_error_messages,
    parse_defs,
)


def _test_info_parse_names_custom_test_body[T: Expression](
    source: str,
    names: str | list[str] | None,
    errors: list[str] | None,
    parse_names: Callable[[TestInfo, T], str | list[str] | None],
) -> None:
    test_info = default_test_info()
    checker = test_info.checker

    source = f"names = {source}"
    node_mapping = parse_defs(source)
    names_node = cast(T, node_mapping["names"])

    assert not checker.errors.is_errors()
    assert parse_names(test_info, names_node) == names
    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def _test_info_parse_names_string_test_body(
    source: str, names: str | list[str] | None, *, errors: list[str] | None = None
) -> None:
    _test_info_parse_names_custom_test_body(source, names, errors, TestInfo.parse_names_string)


def test_test_info_parse_names_string_empty() -> None:
    _test_info_parse_names_string_test_body("''", [])


def test_test_info_parse_names_string_noise_only() -> None:
    _test_info_parse_names_string_test_body("',, , , ,  '", [])


def test_test_info_parse_names_string_one_item() -> None:
    _test_info_parse_names_string_test_body("'bar'", "bar")


def test_test_info_parse_names_string_one_item_extra_noise() -> None:
    _test_info_parse_names_string_test_body("', foo_8,,, , '", "foo_8")


def test_test_info_parse_names_string_three_items() -> None:
    _test_info_parse_names_string_test_body("'a, b_, __c'", ["a", "b_", "__c"])


def test_test_info_parse_names_string_two_items_extra_noise() -> None:
    _test_info_parse_names_string_test_body("',  aa ,b,b,    ,,,,,,,,d  '", ["aa", "b", "b", "d"])


def test_info_parse_names_string_starting_with_number() -> None:
    _test_info_parse_names_string_test_body("'8ac'", None, errors=["invalid-argname"])


def test_test_info_parse_names_string_with_space() -> None:
    _test_info_parse_names_string_test_body("'aa b'", None, errors=["invalid-argname"])


def test_test_info_parse_names_string_with_invalid_name() -> None:
    _test_info_parse_names_string_test_body("'aaa, b b, c'", None, errors=["invalid-argname"])


def test_test_info_parse_names_string_with_multiple_invalid_names() -> None:
    _test_info_parse_names_string_test_body(
        "'aaa, b b, c-d'", None, errors=["invalid-argname", "invalid-argname"]
    )


def _test_info_parse_names_sequence_test_body(
    source: str,
    names: list[str] | None,
    *,
    errors: list[str] | None = None,
) -> None:
    _test_info_parse_names_custom_test_body(source, names, errors, TestInfo.parse_names_sequence)


def test_test_info_parse_names_sequence_empty() -> None:
    _test_info_parse_names_sequence_test_body("()", [])


def test_test_info_parse_names_sequence_integer_name() -> None:
    _test_info_parse_names_sequence_test_body("[5]", None, errors=["unreadable-argname"])


def test_test_info_parse_names_sequence_one_item() -> None:
    _test_info_parse_names_sequence_test_body("['bar']", ["bar"])


def test_test_info_parse_names_sequence_one_item_extra_space() -> None:
    _test_info_parse_names_sequence_test_body("['foo ']", None, errors=["invalid-argname"])


def test_test_info_parse_names_sequence_three_items() -> None:
    _test_info_parse_names_sequence_test_body("('a', 'b_', '__c_')", ["a", "b_", "__c_"])


def test_test_info_parse_names_sequence_one_starting_with_number() -> None:
    _test_info_parse_names_sequence_test_body("['8ac']", None, errors=["invalid-argname"])


def test_test_info_parse_names_sequence_multiple_errors() -> None:
    _test_info_parse_names_sequence_test_body(
        "('a', 10, '28', f'{5}')",
        None,
        # unreadable argname message not repeated
        errors=["unreadable-argname", "invalid-argname"],
    )


def test_test_info_parse_names_sequence_one_int() -> None:
    _test_info_parse_names_sequence_test_body("('a', 10, 'c')", None, errors=["unreadable-argname"])


def test_test_info_parse_names_sequence_one_invalid() -> None:
    _test_info_parse_names_sequence_test_body("('a', '8ab', 'c')", None, errors=["invalid-argname"])


def test_test_info_parse_names_sequence_one_undeterminable() -> None:
    _test_info_parse_names_sequence_test_body(
        "('a', 'ab'.upper(), 'c')", None, errors=["unreadable-argname"]
    )


def _test_info_parse_names_test_body(
    source: str,
    names: list[str] | str | None,
    *,
    errors: list[str] | None = None,
) -> None:
    _test_info_parse_names_custom_test_body(source, names, errors, TestInfo._parse_names)


def test_test_info_parse_names_one_as_string() -> None:
    _test_info_parse_names_test_body("'abc'", "abc")


def test_test_info_parse_names_multiple_as_string() -> None:
    _test_info_parse_names_test_body("'a,b,c'", ["a", "b", "c"])


def test_test_info_parse_names_one_as_sequence() -> None:
    _test_info_parse_names_test_body("['foo']", ["foo"])


def test_test_info_parse_names_many_as_sequence() -> None:
    _test_info_parse_names_test_body("('foo', 'bar')", ["foo", "bar"])


def test_test_info_parse_names_invalid_type() -> None:
    _test_info_parse_names_test_body("{'a', 'b'}", None, errors=["unreadable-argnames"])


def _test_info_from_fn_def_test_body(source: str, *, errors: list[str] | None = None) -> None:
    checker = default_type_checker()

    node_mapping = parse_defs(source)
    test_node = cast(FuncDef, node_mapping["test_info"])

    assert not checker.errors.is_errors()
    test_info = TestInfo.from_fn_def(test_node, checker=checker)

    messages = get_error_messages(checker)
    if errors is None:
        assert test_info is not None, messages
    else:
        assert test_info is None
    check_error_messages(messages, errors=errors)


def test_test_info_from_fn_def_no_args() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info() -> None:
            ...
        """
    )


def test_test_info_from_fn_def_one_arg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(x: int):
            ...
        """
    )


def test_test_info_from_fn_def_keyword_arg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(*, x: int) -> None:
            ...
        """
    )


def test_test_info_from_fn_def_many_args() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info[T: int](x: T, y: T, z: int = 4) -> None:
            ...
        """
    )


def test_test_info_from_fn_def_pos_only_arg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(x, /) -> None:
            ...
        """,
        errors=["pos-only-arg"],
    )


def test_test_info_from_fn_def_vararg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(arg: object, *args: object) -> None:
            ...
        """,
        errors=["var-pos-arg"],
    )


def test_test_info_from_fn_def_varkwarg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(arg: object, **kwargs: object) -> None:
            ...
        """,
        errors=["var-keyword-arg"],
    )


def test_test_info_from_fn_def_vararg_and_varkwarg() -> None:
    _test_info_from_fn_def_test_body(
        """
        def test_info(*args: object, **kwargs: object) -> None:
            ...
        """,
        errors=["var-pos-arg", "var-keyword-arg"],
    )
