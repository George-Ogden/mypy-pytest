from mypy.nodes import ListExpr, TupleExpr

from .many_items_test_signature import ManyItemsTestSignature
from .test_utils import (
    test_signature_custom_check_test_body,
    test_signature_custom_signature_test_body,
)


def _many_items_test_signature_items_signature_test_body(fn_def: str) -> None:
    test_signature_custom_signature_test_body(fn_def, attr="items_signature", extra_expected=False)


def test_many_items_test_signature_items_signature_no_args() -> None:
    _many_items_test_signature_items_signature_test_body(
        """
        def test_case() -> None:
            ...
        """
    )


def test_many_items_test_signature_items_signature_one_arg() -> None:
    _many_items_test_signature_items_signature_test_body(
        """
        def test_case(x: int) -> None:
            ...
        """
    )


def test_many_items_test_signature_items_signature_multiple_args() -> None:
    _many_items_test_signature_items_signature_test_body(
        """
        def test_case(x: int, y: float, z: str) -> None:
            ...
        """
    )


def test_many_items_test_signature_items_signature_multiple_args_generic() -> None:
    _many_items_test_signature_items_signature_test_body(
        """
        def test_case[T, S: int](x: T, y: T, z: S) -> None:
            ...
        """
    )


def _many_items_test_signature_test_case_signature_test_body(fn_defs: str) -> None:
    test_signature_custom_signature_test_body(
        fn_defs, attr="test_case_signature", extra_expected=True
    )


def test_many_test_signature_test_case_signature_no_args() -> None:
    _many_items_test_signature_test_case_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case() -> None:
            ...

        def expected(_: tuple[()] | ParameterSet[()], /) -> None:
            ...
        """
    )


def test_many_items_test_signature_test_case_signature_one_arg() -> None:
    _many_items_test_signature_test_case_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x: float) -> None:
            ...

        def expected(_: tuple[float] | ParameterSet[float], /) -> None:
            ...
        """
    )


def test_many_test_signature_test_case_signature_multiple_args() -> None:
    _many_items_test_signature_test_case_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x: float, z: bool, t: list) -> None:
            ...

        def expected(x: tuple[float, bool, list] | ParameterSet[float, bool, list], /) -> None:
            ...
        """
    )


def test_many_test_signature_test_case_signature_multiple_args_generic() -> None:
    _many_items_test_signature_test_case_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from collections.abc import Iterable

        def test_case[T, I: Iterable](x: I, y: T) -> None:
            ...

        def expected[T, I: Iterable](_: tuple[I, T] | ParameterSet[I, T], /) -> None:
            ...
        """
    )


def _many_items_test_signature_sequence_signature_test_body(fn_defs: str) -> None:
    test_signature_custom_signature_test_body(
        fn_defs, attr="sequence_signature", extra_expected=True
    )


def test_many_items_test_signature_sequence_signature_no_args() -> None:
    _many_items_test_signature_sequence_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from collections.abc import Iterable

        def test_case() -> None:
            ...

        def expected(x: Iterable[tuple[()] | ParameterSet[()]], /) -> None:
            ...
        """
    )


def test_many_items_test_signature_sequence_signature_one_arg() -> None:
    _many_items_test_signature_sequence_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from collections.abc import Iterable

        def test_case(_: None) -> None:
            ...

        def expected(_: Iterable[tuple[None] | ParameterSet[None]], /) -> None:
            ...
        """
    )


def test_many_items_test_signature_sequence_signature_multiple_args() -> None:
    _many_items_test_signature_sequence_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from collections.abc import Iterable, Sequence
        from typing import Any

        def test_case(x: tuple[int, ...], z: Any, t: Sequence[set[int]]) -> None:
            ...

        def expected(_: Iterable[tuple[tuple[int, ...], Any, Sequence[set[int]]] | ParameterSet[tuple[int, ...], Any, Sequence[set[int]]]], /) -> None:
            ...
        """
    )


def test_many_items_test_signature_sequence_signature_multiple_args_generic() -> None:
    _many_items_test_signature_sequence_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from collections.abc import Iterable

        def test_case[T](x: tuple[T, ...], y: int) -> T:
            return x[y]

        def expected[T](_: Iterable[tuple[tuple[T, ...], int] | ParameterSet[tuple[T, ...], int]], /) -> None:
            ...
        """
    )


def _many_items_test_signature_check_items_test_body(defs: str, *, passes: bool) -> None:
    test_signature_custom_check_test_body(
        defs,
        passes,
        ManyItemsTestSignature.check_items,
        bound=TupleExpr | ListExpr,  # type: ignore
    )


def test_many_items_test_signature_check_items_no_args_no_vals_tuple() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case() -> None:
            ...

        vals = ()

        """,
        passes=True,
    )


def test_many_items_test_signature_check_items_no_args_no_vals_list() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case() -> None:
            ...

        vals: list = []

        """,
        passes=True,
    )


def test_many_items_test_signature_check_items_no_args_one_val_list() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case() -> None:
            ...

        vals = [()]

        """,
        passes=False,
    )


def test_many_items_test_signature_check_items_no_args_many_vals_tuple() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case() -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=False,
    )


def test_many_items_test_signature_check_items_many_args_no_vals_tuple() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case(x, y) -> None:
            ...

        vals = ()

        """,
        passes=False,
    )


def test_many_items_test_signature_check_items_many_args_no_vals_list() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case(x, y) -> None:
            ...

        vals: list = []

        """,
        passes=False,
    )


def test_many_items_test_signature_check_items_many_args_correct_vals_list() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case(x, y) -> None:
            ...

        vals: list = [1, ()]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_items_many_args_correct_vals_tuple() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case(x: tuple[()], y: str, z: float) -> None:
            ...

        vals = ((), "blah", 3.14)

        """,
        passes=True,
    )


def test_many_items_test_signature_check_items_many_args_incorrect_val_types_tuple() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case(x: bool, y: str, z: float) -> None:
            ...

        vals = ((), "blah", ())

        """,
        passes=False,
    )


def test_many_items_test_signature_check_items_many_args_incorrect_val_types_list() -> None:
    _many_items_test_signature_check_items_test_body(
        """
        def test_case(y: str, z: float) -> None:
            ...

        vals = [0, 1.0]

        """,
        passes=False,
    )


def _many_items_test_signature_check_test_case_test_body(defs: str, *, passes: bool) -> None:
    test_signature_custom_check_test_body(defs, passes, ManyItemsTestSignature.check_test_case)


def test_many_items_test_signature_check_test_case_no_args_no_vals_tuple() -> None:
    _many_items_test_signature_check_test_case_test_body(
        """
        def test_case() -> None:
            ...

        vals = ()

        """,
        passes=True,
    )


def test_many_items_test_signature_check_test_case_no_args_expression() -> None:
    _many_items_test_signature_check_test_case_test_body(
        """
        def test_case() -> None:
            ...

        vals = [()][0]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_test_case_no_args_incorrect_expression() -> None:
    _many_items_test_signature_check_test_case_test_body(
        """
        def test_case() -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=False,
    )


def test_many_items_test_signature_check_test_case_multiple_args_correct_expression() -> None:
    _many_items_test_signature_check_test_case_test_body(
        """
        def test_case(x: int, y: int, z: int) -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=True,
    )


def test_many_items_test_signature_check_test_case_multiple_args_incorrect_expression() -> None:
    _many_items_test_signature_check_test_case_test_body(
        """
        def test_case(x: int, y: int, z: int) -> None:
            ...

        vals = (1, 2, "c")

        """,
        passes=False,
    )


def test_many_items_test_signature_check_test_case_multiple_args_incorrect_list_expression() -> (
    None
):
    _many_items_test_signature_check_test_case_test_body(
        """
        def test_case(x: int, y: int, z: int) -> None:
            ...

        vals = [1, 2, 3]

        """,
        passes=False,
    )


def _many_items_test_signature_check_sequence_test_body(defs: str, *, passes: bool) -> None:
    test_signature_custom_check_test_body(defs, passes, ManyItemsTestSignature.check_sequence)


def test_many_items_test_signature_check_sequence_no_args_no_vals_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case() -> None:
            ...

        vals = [(), (), (), ParameterSet.__test_init__()]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_sequence_no_args_no_vals_incorrect_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        def test_case() -> None:
            ...

        vals = [(), (3,), (), ()]

        """,
        passes=False,
    )


def test_many_items_test_signature_check_sequence_no_args_no_vals_extra_param() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case() -> None:
            ...

        vals = [(), ParameterSet.__test_init__(()), (), ()]

        """,
        passes=False,
    )


def test_many_items_test_signature_check_sequence_one_arg_nested_val_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = [(1,), (2,)]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_sequence_one_arg_flat_param_spec() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x: int) -> None:
            ...

        vals = [ParameterSet.__test_init__(1), (2,)]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_sequence_one_arg_flat_val_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = [1, 2, 3, 4]

        """,
        passes=False,
    )


def test_many_items_test_signature_check_sequence_one_arg_incorrect_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = ["a", "b"]

        """,
        passes=False,
    )


def test_many_items_test_signature_check_sequence_multiple_args_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = [(2, "a"), (3, "b")]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_sequence_multiple_args_list_params() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        import pytest
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x: int, y: str) -> None:
            ...

        vals = [ParameterSet.__test_init__(2, "a"), ParameterSet.__test_init__(3, "b", marks=[pytest.mark.skip])]

        """,
        passes=True,
    )


def test_many_items_test_signature_check_sequence_multiple_args_incorrect_list() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        def test_case(x: str, y: int) -> None:
            ...

        vals = [(2, "a"), (3, "b")]

        """,
        passes=False,
    )


def test_many_items_test_signature_check_sequence_multiple_args_incorrect_list_params() -> None:
    _many_items_test_signature_check_sequence_test_body(
        """
        import pytest
        from mypy_pytest_plugin_types import ParameterSet

        def test_case(x: int, y: str) -> None:
            ...

        vals = [ParameterSet.__test_init__("x", 0, marks=[pytest.mark.skip])]

        """,
        passes=False,
    )
