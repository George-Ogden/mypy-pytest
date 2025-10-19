from typing import Callable, Literal

from mypy.nodes import Expression, ListExpr, TupleExpr
from mypy.subtypes import is_same_type
from mypy.types import CallableType
import pytest

from .test_signature import TestSignature
from .test_utils import (
    get_signature_and_vals,
    parse_types,
    test_signature_from_fn_type,
    type_checks,
)


def _test_signature_custom_signature_test_body(
    fn_defs: str,
    *,
    attr: Literal["items_signature", "test_case_signature", "sequence_signature"],
    extra_expected: bool,
) -> None:
    type_checker, fn_types = parse_types(fn_defs)
    fn_type = fn_types["test_case"]
    assert isinstance(fn_type, CallableType)
    test_signature = test_signature_from_fn_type(type_checker, fn_name="test_case", fn_type=fn_type)

    expected_key = "expected" if extra_expected else "test_case"
    expected_type = fn_types[expected_key]
    assert expected_type is not None
    assert is_same_type(getattr(test_signature, attr), expected_type)


def _test_signature_items_signature_test_body(fn_def: str) -> None:
    _test_signature_custom_signature_test_body(fn_def, attr="items_signature", extra_expected=False)


def test_test_signature_items_signature_no_args() -> None:
    _test_signature_items_signature_test_body(
        """
        def test_case() -> None:
            ...
        """
    )


def test_test_signature_items_signature_one_arg() -> None:
    _test_signature_items_signature_test_body(
        """
        def test_case(x: int) -> None:
            ...
        """
    )


def test_test_signature_items_signature_multiple_args() -> None:
    _test_signature_items_signature_test_body(
        """
        def test_case(x: int, y: float, z: str) -> None:
            ...
        """
    )


def _test_signature_test_case_signature_test_body(fn_defs: str) -> None:
    _test_signature_custom_signature_test_body(
        fn_defs, attr="test_case_signature", extra_expected=True
    )


def test_test_signature_test_case_signature_no_args() -> None:
    _test_signature_test_case_signature_test_body(
        """
        def test_case() -> None:
            ...

        def expected(x: tuple[()], /) -> None:
            ...
        """
    )


def test_test_signature_test_case_signature_one_arg() -> None:
    _test_signature_test_case_signature_test_body(
        """
        def test_case(x: float) -> None:
            ...

        def expected(x: tuple[float], /) -> None:
            ...
        """
    )


def test_test_signature_test_case_signature_multiple_args() -> None:
    _test_signature_test_case_signature_test_body(
        """
        def test_case(x: float, z: bool, t: list) -> None:
            ...

        def expected(x: tuple[float, bool, list], /) -> None:
            ...
        """
    )


def _test_signature_sequence_signature_test_body(fn_defs: str) -> None:
    _test_signature_custom_signature_test_body(
        fn_defs, attr="sequence_signature", extra_expected=True
    )


def test_test_signature_sequence_signature_no_args() -> None:
    _test_signature_sequence_signature_test_body(
        """
        from collections.abc import Iterable

        def test_case() -> None:
            ...

        def expected(x: Iterable[tuple[()]], /) -> None:
            ...
        """
    )


def test_test_signature_sequence_signature_one_arg() -> None:
    _test_signature_sequence_signature_test_body(
        """
        from collections.abc import Iterable

        def test_case(_: None) -> None:
            ...

        def expected(x: Iterable[None], /) -> None:
            ...
        """
    )


def test_test_signature_sequence_signature_multiple_args() -> None:
    _test_signature_sequence_signature_test_body(
        """
        from collections.abc import Iterable, Sequence
        from typing import Any

        def test_case(x: tuple[int, ...], z: Any, t: Sequence[set[int]]) -> None:
            ...

        def expected(x: Iterable[tuple[tuple[int, ...], Any, Sequence[set[int]]]], /) -> None:
            ...
        """
    )


def _test_signature_custom_check_test_body[T: Expression](
    defs: str,
    passes: bool,
    body: Callable[[TestSignature, T], None],
    *,
    bound: type[T] = Expression,  # type: ignore
) -> None:
    test_signature, val = get_signature_and_vals(defs)
    assert isinstance(val, bound)

    assert (
        type_checks(
            lambda: body(test_signature, val),
            checker=test_signature.checker,
        )
        == passes
    )


def _test_signature_check_one_item_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_custom_check_test_body(defs, passes, TestSignature.check_one_item)


def _test_signature_check_many_items_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_custom_check_test_body(
        defs,
        passes,
        TestSignature.check_many_items,
        bound=TupleExpr | ListExpr,  # type: ignore
    )


def test_test_signature_check_items_no_args_no_vals_tuple() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case() -> None:
            ...

        vals = ()

        """,
        passes=True,
    )


def test_test_signature_check_items_no_args_no_vals_list() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case() -> None:
            ...

        vals: list = []

        """,
        passes=True,
    )


def test_test_signature_check_items_no_args_one_val_list() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case() -> None:
            ...

        vals = [()]

        """,
        passes=False,
    )


def test_test_signature_check_items_no_args_many_vals_tuple() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case() -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=False,
    )


def test_test_signature_check_items_one_arg_one_val_tuple() -> None:
    _test_signature_check_one_item_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = 3

        """,
        passes=True,
    )


def test_test_signature_check_items_one_arg_incorrect_val_tuple() -> None:
    _test_signature_check_one_item_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = "s"

        """,
        passes=False,
    )


def test_test_signature_check_items_many_args_no_vals_tuple() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x, y) -> None:
            ...

        vals = ()

        """,
        passes=False,
    )


def test_test_signature_check_items_many_args_no_vals_list() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x, y) -> None:
            ...

        vals: list = []

        """,
        passes=False,
    )


def test_test_signature_check_items_many_args_correct_vals_list() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x, y) -> None:
            ...

        vals: list = [1, ()]

        """,
        passes=True,
    )


def test_test_signature_check_items_many_args_correct_vals_tuple() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x: tuple[()], y: str, z: float) -> None:
            ...

        vals = ((), "blah", 3.14)

        """,
        passes=True,
    )


def test_test_signature_check_items_many_args_incorrect_val_types_tuple() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x: bool, y: str, z: float) -> None:
            ...

        vals = ((), "blah", ())

        """,
        passes=False,
    )


def test_test_signature_check_items_many_args_incorrect_val_types_list() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(y: str, z: float) -> None:
            ...

        vals = [0, 1.0]

        """,
        passes=False,
    )


def _test_signature_check_test_case_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_custom_check_test_body(defs, passes, TestSignature.check_test_case)


def test_test_signature_check_test_case_no_args_no_vals_tuple() -> None:
    _test_signature_check_test_case_test_body(
        """
        def test_case() -> None:
            ...

        vals = ()

        """,
        passes=True,
    )


def test_test_signature_check_test_case_no_args_expression() -> None:
    _test_signature_check_test_case_test_body(
        """
        def test_case() -> None:
            ...

        vals = [()][0]

        """,
        passes=True,
    )


def test_test_signature_check_test_case_no_args_incorrect_expression() -> None:
    _test_signature_check_test_case_test_body(
        """
        def test_case() -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=False,
    )


def test_test_signature_check_test_case_one_arg_correct_expression() -> None:
    with pytest.raises(AssertionError):
        _test_signature_check_test_case_test_body(
            """
            def test_case(x: int) -> None:
                ...

            vals = (3,)

            """,
            passes=True,
        )


def test_test_signature_check_test_case_multiple_args_correct_expression() -> None:
    _test_signature_check_test_case_test_body(
        """
        def test_case(x: int, y: int, z: int) -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=True,
    )


def test_test_signature_check_test_case_multiple_args_incorrect_expression() -> None:
    _test_signature_check_test_case_test_body(
        """
        def test_case(x: int, y: int, z: int) -> None:
            ...

        vals = (1, 2, "c")

        """,
        passes=False,
    )


def test_test_signature_check_test_case_multiple_args_incorrect_list_expression() -> None:
    _test_signature_check_test_case_test_body(
        """
        def test_case(x: int, y: int, z: int) -> None:
            ...

        vals = [1, 2, 3]

        """,
        passes=False,
    )


def _test_signature_check_sequence_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_custom_check_test_body(defs, passes, TestSignature.check_sequence)


def test_test_signature_check_sequence_no_args_no_vals_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case() -> None:
            ...

        vals = [(), (), (), ()]

        """,
        passes=True,
    )


def test_test_signature_check_sequence_no_args_no_vals_incorrect_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case() -> None:
            ...

        vals = [(), (3, ), (), ()]

        """,
        passes=False,
    )


def test_test_signature_check_sequence_one_arg_one_val_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = [1, 2, 3, 4]

        """,
        passes=True,
    )


def test_test_signature_check_sequence_one_arg_nested_val_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = [(1,), (2,)]

        """,
        passes=False,
    )


def test_test_signature_check_sequence_one_arg_incorrect_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = ["a", "b"]

        """,
        passes=False,
    )


def test_test_signature_check_sequence_multiple_args_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = [(2, "a"), (3, "b")]

        """,
        passes=True,
    )


def test_test_signature_check_sequence_multiple_args_incorrect_list() -> None:
    _test_signature_check_sequence_test_body(
        """
        def test_case(x: str, y: int) -> None:
            ...

        vals = [(2, "a"), (3, "b")]

        """,
        passes=False,
    )
