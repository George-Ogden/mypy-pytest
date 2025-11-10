from typing import Callable, cast

from mypy.nodes import Expression, FuncDef
from mypy.types import CallableType
import pytest

from .test_info import TestInfo
from .test_utils import (
    check_error_messages,
    default_test_info,
    get_error_messages,
    parse,
    test_info_from_defs,
    test_signature_from_fn_type,
)


def _test_info_parse_names_custom_test_body[T: Expression](
    source: str,
    names: str | list[str] | None,
    errors: list[str] | None,
    parse_names: Callable[[TestInfo, T], str | list[str] | None],
) -> None:
    source = f"names = {source}"
    parse_result = parse(source)
    checker = parse_result.checker

    names_node = cast(T, parse_result.defs["names"])

    test_info = default_test_info(checker)

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


def test_test_info_parse_names_duplicate_name() -> None:
    _test_info_parse_names_test_body("'a, b, a'", None, errors=["duplicate-argname"])


def test_test_info_parse_names_invalid_type() -> None:
    _test_info_parse_names_test_body("{'a', 'b'}", None, errors=["unreadable-argnames"])


def _test_info_from_fn_def_test_body(source: str, *, errors: list[str] | None = None) -> None:
    parse_result = parse(source)
    checker = parse_result.checker

    test_node = parse_result.defs["test_info"]
    assert isinstance(test_node, FuncDef)

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


def _test_info_sub_signature_test_body(
    defs: str, argnames: str | list[str], *, errors: list[str] | None = None
) -> None:
    parse_result = parse(defs)
    checker = parse_result.checker

    fn_type = parse_result.types.get("sub_signature")
    assert isinstance(fn_type, CallableType | None)
    expected_signature = (
        None
        if fn_type is None
        else test_signature_from_fn_type(checker, fn_name="test_info", fn_type=fn_type)
    )

    test_info = test_info_from_defs(defs, name="test_info")

    assert not checker.errors.is_errors()
    sub_signature = test_info.sub_signature(argnames)

    messages = get_error_messages(checker)
    assert sub_signature == expected_signature, messages

    check_error_messages(messages, errors=errors)


def test_test_info_sub_signature_no_args() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info() -> None:
            ...

        def sub_signature() -> None:
            ...
        """,
        argnames=[],
    )


def test_test_info_sub_signature_single_arg() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info(x: int, y: bool) -> None:
            ...

        def sub_signature(x_1: int) -> None:
            ...
        """,
        argnames="x",
    )


def test_test_info_sub_signature_single_arg_sequence() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info(x: int, y: bool) -> None:
            ...

        def sub_signature(y: bool) -> None:
            ...
        """,
        argnames=["y"],
    )


def test_test_info_sub_signature_multiple_args() -> None:
    _test_info_sub_signature_test_body(
        """
        def test_info(x: int, y: bool, z: str) -> None:
            ...

        def sub_signature(z: str, x: int) -> None:
            ...
        """,
        argnames=["z", "x"],
    )


def _test_info_check_decorator_test_body(defs: str, *, errors: list[str] | None = None) -> None:
    test_info = test_info_from_defs(defs, name="test_info")
    assert test_info is not None
    [decorator] = test_info.decorators
    checker = test_info.checker

    assert not checker.errors.is_errors()
    test_info.check_decorator(decorator)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_test_info_check_decorator_no_errors() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            "x", [1, 2, 3, 4]
        )
        def test_info(x: int) -> None:
            ...
        """)


def test_test_info_check_decorator_no_errors_flipped_args() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            argvalues="abcd",
            argnames="x",
            ids="dcba",
        )
        def test_info(x: str) -> None:
            ...
        """)


def test_test_info_check_decorator_shared_argnames() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            *("x", [])
        )
        def test_info(x: float) -> None:
            ...
        """,
        errors=["variadic-argnames-argvalues"],
    )


def test_test_info_check_decorator_shared_argnames_beyond_limit() -> None:
    with pytest.raises(TypeError):
        _test_info_check_decorator_test_body(
            """
            import pytest

            @pytest.mark.parametrize(
                "x", *((), ())
            )
            def test_info(x: float) -> None:
                ...
            """,
            errors=["variadic-argnames-argvalues"],
        )


def test_test_info_check_decorator_shared_argnames_as_dict() -> None:
    with pytest.raises(TypeError):
        _test_info_check_decorator_test_body(
            """
            import pytest

            @pytest.mark.parametrize(
                argvalues=[True, False],
                **dict(argnames="x", ids=[1, 0])
            )
            def test_info(x: bool) -> None:
                ...
            """,
            errors=["variadic-argnames-argvalues"],
        )


def test_test_info_check_decorator_wrapped_argvalues() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "x", *([True, False],)
        )
        def test_info(x: bool) -> None:
            ...
        """,
        errors=["variadic-argnames-argvalues"],
    )


def test_test_info_check_decorator_no_errors_unusual_types() -> None:
    _test_info_check_decorator_test_body("""
        import pytest

        @pytest.mark.parametrize(
            "x", iter([True, False])
        )
        def test_info(x: bool) -> None:
            ...
    """)


def test_test_info_check_decorator_invalid_argname() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "foo", [1, 2, 3]
        )
        def test_info(bar: int) -> None:
            ...
        """,
        errors=["unknown-argname"],
    )


def test_test_info_check_decorator_invalid_type() -> None:
    _test_info_check_decorator_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "x", [1, 2, 3]
        )
        def test_info(x: str) -> None:
            ...
        """,
        errors=["arg-type"],
    )


def _test_info_check_test_body(defs: str, *, errors: list[str] | None = None) -> None:
    test_info = test_info_from_defs(defs, name="test_info")
    assert test_info is not None
    checker = test_info.checker

    assert not checker.errors.is_errors()
    test_info.check()

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_test_info_check_no_decorators_no_arguments() -> None:
    _test_info_check_test_body(
        """
        def test_info() -> None:
            ...
        """
    )


def test_test_info_check_no_decorators_missing_argnames() -> None:
    _test_info_check_test_body(
        """
        def test_info(foo) -> None:
            ...
        """,
        errors=["missing-argname"],
    )


def test_test_info_check_single_decorator_valid_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ("foo",),
            [
                "bar",
                10,
                False
            ]
        )
        def test_info(foo) -> None:
            ...
        """
    )


def test_test_info_check_multiple_decorators_valid_split_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            "abcdefg"
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """
    )


def test_test_info_check_multiple_decorators_missing_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            "abcdefg"
        )
        def test_info(x: int, y: str, z: float, missing1, missing2) -> None:
            ...
        """,
        errors=["missing-argname", "missing-argname"],
    )


def test_test_info_check_multiple_decorators_repeated_argnames() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "x, y",
            [
                (1, "1"),
                (5, "2"),
            ]
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """,
        errors=["repeated-argname"],
    )


def test_test_info_check_multiple_decorators_single_type_error() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            ["x", "z"],
            [
                (1, 2.0),
                (5, 3.0),
            ]
        )
        @pytest.mark.parametrize(
            "y",
            [["abcde"]]
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """,
        errors=["arg-type"],
    )


def test_test_info_check_multiple_decorators_multiple_type_errors() -> None:
    _test_info_check_test_body(
        """
        import pytest

        @pytest.mark.parametrize(
            "x",
            [1, 2, 8.0]
        )
        @pytest.mark.parametrize(
            "y",
            ["a", "b", False]
        )
        @pytest.mark.parametrize(
            "z",
            [object(), 1.0, "no", 2.0]
        )
        def test_info(x: int, y: str, z: float) -> None:
            ...
        """,
        errors=["arg-type"] * 4,
    )
