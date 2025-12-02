from .one_item_test_signature import OneItemTestSignature
from .test_utils import (
    test_signature_custom_check_test_body,
    test_signature_custom_signature_test_body,
)


def _one_item_test_signature_test_case_signature_test_body(defs: str) -> None:
    test_signature_custom_signature_test_body(defs, attr="test_case_signature", extra_expected=True)


def test_one_item_test_signature_test_case_signature() -> None:
    _one_item_test_signature_test_case_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet

        def test_case(x_1: float) -> None:
            ...

        def expected(x: float | ParameterSet[float]) -> None:
            ...
        """,
    )


def test_one_item_test_signature_test_case_signature_generic() -> None:
    _one_item_test_signature_test_case_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case[T](x_1: T) -> None:
            ...

        def expected[T](x: T | ParameterSet[T]) -> None:
            ...
        """,
    )


def _one_item_test_signature_sequence_signature_test_body(defs: str) -> None:
    test_signature_custom_signature_test_body(defs, attr="sequence_signature", extra_expected=True)


def test_one_item_test_signature_sequence_signature() -> None:
    _one_item_test_signature_sequence_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from typing import Iterable

        def test_case(x_1: int) -> None:
            ...

        def expected(_: Iterable[int | ParameterSet[int]], /) -> None:
            ...
        """,
    )


def test_one_item_test_signature_sequence_signature_generic() -> None:
    _one_item_test_signature_sequence_signature_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        from typing import Iterable

        def test_case[T: int](x_1: T) -> None:
            ...

        def expected[T: int](_: Iterable[T | ParameterSet[T]], /) -> None:
            ...
        """,
    )


def _one_item_test_signature_check_test_case_test_body(defs: str, *, passes: bool) -> None:
    test_signature_custom_check_test_body(defs, passes, OneItemTestSignature.check_test_case)


def test_one_item_test_signature_check_test_case_one_val() -> None:
    _one_item_test_signature_check_test_case_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = 3

        """,
        passes=True,
    )


def test_one_item_test_signature_check_test_case_one_param() -> None:
    _one_item_test_signature_check_test_case_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x_1: int) -> None:
            ...

        vals = ParameterSet.__test_init__(3)

        """,
        passes=True,
    )


def test_one_item_test_signature_check_test_case_incorrect_val() -> None:
    _one_item_test_signature_check_test_case_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = "s"

        """,
        passes=False,
    )


def test_one_item_test_signature_check_test_case_incorrect_val_tuple() -> None:
    _one_item_test_signature_check_test_case_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = (4,)

        """,
        passes=False,
    )


def test_one_item_test_signature_check_test_case_incorrect_param_tuple() -> None:
    _one_item_test_signature_check_test_case_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x_1: int) -> None:
            ...

        vals = ParameterSet.__test_init__((4,))

        """,
        passes=False,
    )


def _one_item_test_signature_check_sequence_test_body(defs: str, *, passes: bool) -> None:
    test_signature_custom_check_test_body(defs, passes, OneItemTestSignature.check_sequence)


def test_one_item_test_signature_check_sequence_flat_val_list() -> None:
    _one_item_test_signature_check_sequence_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = [1, 2, 3, 4]

        """,
        passes=True,
    )


def test_one_item_test_signature_check_sequence_flat_param_list() -> None:
    _one_item_test_signature_check_sequence_test_body(
        """
        from mypy_pytest_plugin_types import ParameterSet
        def test_case(x_1: int) -> None:
            ...

        vals = [1, ParameterSet.__test_init__(2,)]

        """,
        passes=True,
    )


def test_one_item_test_signature_check_sequence_nested_val_list() -> None:
    _one_item_test_signature_check_sequence_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = [(1,), (2,)]

        """,
        passes=False,
    )
