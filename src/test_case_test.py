from .test_case import TestCase
from .test_utils import get_signature_and_vals, type_checks


def _test_signature_check_one_item_test_body(defs: str, *, passes: bool) -> None:
    test_signature, val = get_signature_and_vals(defs)
    test_case = TestCase(val)

    assert (
        type_checks(
            lambda: test_case.check_one_item_against(test_signature), checker=test_signature.checker
        )
        == passes
    )


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
