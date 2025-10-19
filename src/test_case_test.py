from collections.abc import Callable

from .test_case import TestCase
from .test_signature import TestSignature
from .test_utils import get_signature_and_vals, type_checks


def _test_signature_check_against_custom_test_body(
    defs: str, passes: bool, body: Callable[[TestCase, TestSignature], None]
) -> None:
    test_signature, val = get_signature_and_vals(defs)
    test_case = TestCase(val)

    assert (
        type_checks(lambda: body(test_case, test_signature), checker=test_signature.checker)
        == passes
    )


def _test_signature_check_one_item_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_check_against_custom_test_body(defs, passes, TestCase.check_one_item_against)


def test_test_case_check_one_item_against_correct() -> None:
    _test_signature_check_one_item_test_body(
        """
        def test_case(x: str) -> None:
            ...

        vals = "s"

        """,
        passes=True,
    )


def _test_signature_check_many_items_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_check_against_custom_test_body(defs, passes, TestCase.check_many_items_against)


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


def _test_signature_check_entire_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_check_against_custom_test_body(defs, passes, TestCase.check_entire_against)


def test_test_case_check_entire_against_correct() -> None:
    _test_signature_check_entire_test_body(
        """
        def test_case(x: tuple, y: tuple) -> None:
            ...

        vals = ((3, 4), (5,))

        """,
        passes=True,
    )


def test_test_case_check_entire_against_incorrect() -> None:
    _test_signature_check_entire_test_body(
        """
        def test_case(x: int, y: int) -> None:
            ...

        vals = [1, 2]

        """,
        passes=False,
    )


def _test_signature_check_multiple_test_body(defs: str, *, passes: bool) -> None:
    _test_signature_check_against_custom_test_body(defs, passes, TestCase.check_multiple_against)


def test_test_case_check_multiple_against_zero_args_empty_tuple() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case() -> None:
            ...

        vals = ()

        """,
        passes=True,
    )


def test_test_case_check_multiple_against_zero_args_empty_list() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case() -> None:
            ...

        vals: list = []

        """,
        passes=True,
    )


def test_test_case_check_multiple_against_zero_args_non_empty_tuple() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case() -> None:
            ...

        vals = ((),)

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_zero_args_non_empty_list() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case() -> None:
            ...

        vals = [()]

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_zero_args_one_item() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case() -> None:
            ...

        vals = "x"

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_many_args_small_sized_tuple() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: int) -> None:
            ...

        vals = ()

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_many_args_large_sized_tuple() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: int) -> None:
            ...

        vals = (1, 2, 3)

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_many_args_large_sized_list() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: int) -> None:
            ...

        vals = [1, 2, 3]

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_many_args_correct_tuple() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = (1, "one")

        """,
        passes=True,
    )


def test_test_case_check_multiple_against_many_args_correct_list() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = [1, "one"]

        """,
        passes=True,
    )


def test_test_case_check_multiple_against_many_args_correct_expression() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = [(2, "two")][0]

        """,
        passes=True,
    )


def test_test_case_check_multiple_against_many_args_incorrect_expression() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = [[2, "two"]][0]

        """,
        passes=False,
    )


def test_test_case_check_multiple_against_many_args_set_expression() -> None:
    _test_signature_check_multiple_test_body(
        """
        def test_case(x: int, y: int) -> None:
            ...

        vals = {4, 5}

        """,
        passes=False,
    )
