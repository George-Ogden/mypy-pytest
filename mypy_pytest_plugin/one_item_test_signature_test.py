from .one_item_test_signature import OneItemTestSignature
from .test_utils import (
    test_signature_custom_check_test_body,
    test_signature_custom_signature_test_body,
)


def test_one_item_test_signature_test_case_signature() -> None:
    test_signature_custom_signature_test_body(
        """
        def test_case(x_1: float) -> None:
            ...

        def expected(x: float) -> None:
            ...
        """,
        attr="test_case_signature",
        extra_expected=True,
    )


def test_one_item_test_signature_sequence_signature() -> None:
    test_signature_custom_signature_test_body(
        """
        from typing import Iterable

        def test_case(x_1: int) -> None:
            ...

        def expected(_: Iterable[int], /) -> None:
            ...
        """,
        attr="sequence_signature",
        extra_expected=True,
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


def test_one_item_test_signature_check_sequence_nested_val_list() -> None:
    _one_item_test_signature_check_sequence_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = [(1,), (2,)]

        """,
        passes=False,
    )
