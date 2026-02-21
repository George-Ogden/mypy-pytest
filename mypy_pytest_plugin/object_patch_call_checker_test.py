from mypy.nodes import CallExpr, Expression
from mypy.subtypes import is_same_type

from .object_patch_call_checker import ObjectPatchCallChecker
from .test_utils import check_error_messages, dump_expr, get_error_messages, parse


def _attribute_arg_test_body(defs: str) -> None:
    parse_result = parse(defs)
    parse_result.accept_all()
    patch_call_checker = ObjectPatchCallChecker(parse_result.checker)

    call = parse_result.defs["call"]
    assert isinstance(call, CallExpr)
    attribute_arg = patch_call_checker._attribute_arg(call)
    expected = parse_result.defs.get("arg", None)
    assert isinstance(expected, Expression | None)

    if expected is None:
        assert attribute_arg is None
    else:
        assert dump_expr(attribute_arg) == dump_expr(expected)


def test_attribute_arg_unreadable() -> None:
    _attribute_arg_test_body(
        """
        from typing import Any, overload

        @overload
        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int) -> int:
            ...

        @overload
        def foo[T](target: Any, attribute: str, test: T) -> int:
            ...

        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int = 0) -> int:
            return extra_arg

        call = foo(foo, "bar", 10, extra_arg=0)
        arg = "bar"
        """
    )


def test_attribute_arg_readable() -> None:
    _attribute_arg_test_body(
        """
        from typing import Any, overload

        @overload
        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int) -> int:
            ...

        @overload
        def foo[T](target: Any, attribute: str, test: T) -> int:
            ...

        def foo[T](target: Any, attribute: str, test: T, *, extra_arg: int = 0) -> int:
            return extra_arg

        call = foo(*(foo, "bar", 10))
        """
    )


def _attribute_type_test_body(
    defs: str, attribute: str, *, errors: list[str] | None = None
) -> None:
    parse_result = parse(defs)
    checker = parse_result.checker
    patch_call_checker = ObjectPatchCallChecker(checker)

    base = parse_result.defs["base"]
    assert isinstance(base, Expression)

    attribute_type = patch_call_checker._attribute_type(base, attribute, context=base)

    expected = parse_result.types.get("expected")
    if expected is None:
        assert attribute_type is None
    else:
        assert attribute_type is not None
        assert is_same_type(attribute_type, expected)

    error_messages = get_error_messages(checker)
    check_error_messages(error_messages, errors=errors)


def test_attribute_type_simple_class() -> None:
    _attribute_type_test_body(
        """
        class Base:
            attribute: int

        base = Base()
        expected: int
        """,
        "attribute",
    )


def test_attribute_type_simple_class_any() -> None:
    _attribute_type_test_body(
        """
        from typing import Any

        class Base:
            attribute: Any

        base = Base()
        expected: Any
        """,
        "attribute",
    )


def test_attribute_type_invalid_base() -> None:
    _attribute_type_test_body(
        """
        base = None
        """,
        "attribute",
        errors=["attr-defined"],
    )


def test_attribute_type_invalid_attribute() -> None:
    _attribute_type_test_body(
        """
        class Base:
            attribute: int

        base = Base()
        """,
        "not_an_attribute",
        errors=["attr-defined"],
    )


def test_attribute_type_fallback() -> None:
    _attribute_type_test_body(
        """
        from typing import Callable, cast

        base = cast(tuple, (3, 4))
        expected = cast(tuple, tuple).__add__
        """,
        "__add__",
    )


def test_attribute_type_union() -> None:
    _attribute_type_test_body(
        """
        from typing import cast, Union

        class F1:
            x: str
        class F2:
            x: int

        base = cast(Union[F1, F2], F1())
        expected: int | str
        """,
        "x",
    )
