from collections.abc import Callable
from typing import cast

from mypy.nodes import Expression

from .argnames_parser import ArgnamesParser
from .test_utils import check_error_messages, default_argnames_parser, get_error_messages, parse


def _argnames_parser_parse_names_custom_test_body[T: Expression](
    source: str,
    names: str | list[str] | None,
    errors: list[str] | None,
    parse_names: Callable[[ArgnamesParser, T], str | list[str] | None],
) -> None:
    source = f"names = {source}"
    parse_result = parse(source)
    checker = parse_result.checker

    names_node = cast(T, parse_result.defs["names"])

    argnames_parser = default_argnames_parser(checker)

    assert not checker.errors.is_errors()
    assert parse_names(argnames_parser, names_node) == names

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def _argnames_parser_parse_names_string_test_body(
    source: str, names: str | list[str] | None, *, errors: list[str] | None = None
) -> None:
    _argnames_parser_parse_names_custom_test_body(
        source, names, errors, ArgnamesParser.parse_names_string
    )


def test_argnames_parser_parse_names_string_empty() -> None:
    _argnames_parser_parse_names_string_test_body("''", [])


def test_argnames_parser_parse_names_string_noise_only() -> None:
    _argnames_parser_parse_names_string_test_body("',, , , ,  '", [])


def test_argnames_parser_parse_names_string_one_item() -> None:
    _argnames_parser_parse_names_string_test_body("'bar'", "bar")


def test_argnames_parser_parse_names_string_one_item_extra_noise() -> None:
    _argnames_parser_parse_names_string_test_body("', foo_8,,, , '", "foo_8")


def test_argnames_parser_parse_names_string_three_items() -> None:
    _argnames_parser_parse_names_string_test_body("'a, b_, __c'", ["a", "b_", "__c"])


def test_argnames_parser_parse_names_string_two_items_extra_noise() -> None:
    _argnames_parser_parse_names_string_test_body(
        "',  aa ,b,b,    ,,,,,,,,d  '", ["aa", "b", "b", "d"]
    )


def argnames_parser_parse_names_string_starting_with_number() -> None:
    _argnames_parser_parse_names_string_test_body("'8ac'", None, errors=["invalid-argname"])


def test_argnames_parser_parse_names_string_with_space() -> None:
    _argnames_parser_parse_names_string_test_body("'aa b'", None, errors=["invalid-argname"])


def test_argnames_parser_parse_names_string_with_invalid_name() -> None:
    _argnames_parser_parse_names_string_test_body("'aaa, b b, c'", None, errors=["invalid-argname"])


def test_argnames_parser_parse_names_string_with_multiple_invalid_names() -> None:
    _argnames_parser_parse_names_string_test_body(
        "'aaa, b b, c-d'", None, errors=["invalid-argname", "invalid-argname"]
    )


def test_argnames_parser_parse_names_string_with_reserved_name() -> None:
    _argnames_parser_parse_names_string_test_body(
        "'request, foo'", None, errors=["request-keyword"]
    )


def _argnames_parser_parse_names_sequence_test_body(
    source: str, names: list[str] | None, *, errors: list[str] | None = None
) -> None:
    _argnames_parser_parse_names_custom_test_body(
        source, names, errors, ArgnamesParser.parse_names_sequence
    )


def test_argnames_parser_parse_names_sequence_empty() -> None:
    _argnames_parser_parse_names_sequence_test_body("()", [])


def test_argnames_parser_parse_names_sequence_integer_name() -> None:
    _argnames_parser_parse_names_sequence_test_body("[5]", None, errors=["unreadable-argname"])


def test_argnames_parser_parse_names_sequence_one_item() -> None:
    _argnames_parser_parse_names_sequence_test_body("['bar']", ["bar"])


def test_argnames_parser_parse_names_sequence_one_item_extra_space() -> None:
    _argnames_parser_parse_names_sequence_test_body("['foo ']", None, errors=["invalid-argname"])


def test_argnames_parser_parse_names_sequence_three_items() -> None:
    _argnames_parser_parse_names_sequence_test_body("('a', 'b_', '__c_')", ["a", "b_", "__c_"])


def test_argnames_parser_parse_names_sequence_one_starting_with_number() -> None:
    _argnames_parser_parse_names_sequence_test_body("['8ac']", None, errors=["invalid-argname"])


def test_argnames_parser_parse_names_sequence_multiple_errors() -> None:
    _argnames_parser_parse_names_sequence_test_body(
        "('a', 10, '28', f'{5}')",
        None,
        # unreadable argname message not repeated
        errors=["unreadable-argname", "invalid-argname"],
    )


def test_argnames_parser_parse_names_sequence_one_int() -> None:
    _argnames_parser_parse_names_sequence_test_body(
        "('a', 10, 'c')", None, errors=["unreadable-argname"]
    )


def test_argnames_parser_parse_names_sequence_one_invalid() -> None:
    _argnames_parser_parse_names_sequence_test_body(
        "('a', '8ab', 'c')", None, errors=["invalid-argname"]
    )


def test_argnames_parser_parse_names_sequence_multiple_keywords() -> None:
    _argnames_parser_parse_names_sequence_test_body(
        "('if', 'it', 'is')", None, errors=["invalid-argname", "invalid-argname"]
    )


def test_argnames_parser_parse_names_sequence_one_undeterminable() -> None:
    _argnames_parser_parse_names_sequence_test_body(
        "('a', 'ab'.upper(), 'c')", None, errors=["unreadable-argname"]
    )


def test_argnames_parser_parse_names_sequence_with_reserved_name() -> None:
    _argnames_parser_parse_names_sequence_test_body(
        "['request', 'foo']", None, errors=["request-keyword"]
    )


def _argnames_parser_parse_names_test_body(
    source: str, names: list[str] | str | None, *, errors: list[str] | None = None
) -> None:
    _argnames_parser_parse_names_custom_test_body(source, names, errors, ArgnamesParser.parse_names)


def test_argnames_parser_parse_names_one_as_string() -> None:
    _argnames_parser_parse_names_test_body("'abc'", "abc")


def test_argnames_parser_parse_names_multiple_as_string() -> None:
    _argnames_parser_parse_names_test_body("'a,b,c'", ["a", "b", "c"])


def test_argnames_parser_parse_names_one_as_sequence() -> None:
    _argnames_parser_parse_names_test_body("['foo']", ["foo"])


def test_argnames_parser_parse_names_many_as_sequence() -> None:
    _argnames_parser_parse_names_test_body("('foo', 'bar')", ["foo", "bar"])


def test_argnames_parser_parse_names_duplicate_name() -> None:
    _argnames_parser_parse_names_test_body("'a, b, a'", None, errors=["duplicate-argname"])


def test_argnames_parser_parse_names_invalid_type() -> None:
    _argnames_parser_parse_names_test_body("{'a', 'b'}", None, errors=["unreadable-argnames"])
