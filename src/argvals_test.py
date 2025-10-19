from collections.abc import Callable

from .argvals import Argvals
from .test_signature import TestSignature
from .test_utils import get_signature_and_vals, type_checks


def _argvals_check_against_custom_sequence_body(
    defs: str, errors: int, body: Callable[[Argvals, TestSignature], None]
) -> None:
    test_signature, vals = get_signature_and_vals(defs)
    argvals = Argvals(vals)

    checker = test_signature.checker
    assert type_checks(lambda: body(argvals, test_signature), checker=checker) == (errors == 0)
    assert checker.errors.num_messages() == errors


def _argvals_check_sequence_test_body(defs: str, *, errors: int) -> None:
    _argvals_check_against_custom_sequence_body(defs, errors, Argvals.check_sequence_against)


def test_argvals_check_sequence_empty() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = ()
        """,
        errors=0,
    )


def test_argvals_check_sequence_one_correct() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case(x: int, y: float) -> None:
            ...

        vals = [(1, 3.5)]
        """,
        errors=0,
    )


def test_argvals_check_sequence_many_correct() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case(x: int, y: float, z: str) -> None:
            ...

        vals = {(1, 3.5, "8"), (2, -1.0, "b"), (3, -5, "d")}
        """,
        errors=0,
    )


def test_argvals_check_sequence_all_but_one_correct() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case(x: int) -> None:
            ...

        vals = {8, 9, 10, "b"}
        """,
        errors=1,
    )


def test_argvals_check_sequence_all_incorrect() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case() -> None:
            ...

        vals = [8, ((),), [""]]
        """,
        errors=3,
    )


def test_argvals_check_sequence_some_incorrect() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case(x: int, y: tuple[()]) -> None:
            ...

        vals = [(9, (), ()), [8, ()], [4]]
        """,
        errors=2,
    )
