from collections.abc import Callable

from .test_case import TestCase
from .test_signature import TestSignature
from .test_utils import get_signature_and_vals, type_checks


def _test_signature_check_items_test_body(
    defs: str, passes: bool, body: Callable[[TestCase, TestSignature], None]
) -> None:
    test_signature, val = get_signature_and_vals(defs)
    test_case = TestCase(val)

    assert (
        type_checks(lambda: body(test_case, test_signature), checker=test_signature.checker)
        == passes
    )


def _test_signature_check_one_item_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_check_items_test_body(defs, passes, TestCase.check_one_item_against)


def _test_signature_check_many_items_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_check_items_test_body(defs, passes, TestCase.check_many_items_against)


def test_test_case_check_one_item_against_correct() -> None:
    _test_signature_check_one_item_test_body(
        """
        def test_case(x: str) -> None:
            ...

        vals = "s"

        """,
        passes=True,
    )


def test_test_case_check_one_item_against_incorrect() -> None:
    _test_signature_check_one_item_test_body(
        """
        def test_case(x: bool) -> None:
            ...

        vals = 3.5

        """,
        passes=False,
    )


def test_test_case_check_many_items_against_correct() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x: float, y: int) -> None:
            ...

        vals = [1.0, 2]

        """,
        passes=True,
    )


def test_test_case_check_many_items_against_incorrect() -> None:
    _test_signature_check_many_items_test_body(
        """
        def test_case(x: float, y: int, z: str) -> None:
            ...

        vals = ["str", 5, -1.1]

        """,
        passes=False,
    )
