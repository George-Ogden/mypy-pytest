from collections.abc import Callable

from .argvals import Argvals
from .test_signature import TestSignature
from .test_utils import get_error_messages, get_signature_and_vals, type_checks


def _argvals_check_against_custom_sequence_body(
    defs: str, errors: int, body: Callable[[Argvals, TestSignature], None]
) -> None:
    test_signature, vals = get_signature_and_vals(defs)
    argvals = Argvals(vals)

    checker = test_signature.checker
    type_check_result = type_checks(lambda: body(argvals, test_signature), checker=checker)
    messages = get_error_messages(checker)
    assert type_check_result == (errors == 0), messages
    assert checker.errors.num_messages() == errors, messages


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
        def test_case(x_1: int) -> None:
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


def test_argvals_check_sequence_correct_nested_sequence() -> None:
    _argvals_check_sequence_test_body(
        """
        def test_case(x: tuple[int]) -> None:
            ...

        vals = (((3,),), ((4,),))
        """,
        errors=0,
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


def _argvals_check_entire_test_body(defs: str, *, errors: int) -> None:
    _argvals_check_against_custom_sequence_body(defs, errors, Argvals.check_entire_against)


def test_argvals_check_entire_correct_expression() -> None:
    _argvals_check_entire_test_body(
        """
        def test_case(x: int, y: float) -> None:
            ...

        vals = [[(2, 3.0), (4, 5.0)]][0]
        """,
        errors=0,
    )


def test_argvals_check_entire_incorrect_expression() -> None:
    _argvals_check_entire_test_body(
        """
        def test_case(x: int, y: str) -> None:
            ...

        vals = [[(1,), (2, 3), ("a", 2)]][0]
        """,
        errors=1,
    )


def _argvals_check_against_test_body(defs: str, *, errors: int) -> None:
    _argvals_check_against_custom_sequence_body(defs, errors, Argvals.check_against)


def test_argvals_check_against_correct_set() -> None:
    _argvals_check_against_test_body(
        """
        def test_case(x: int, y: str, z: tuple[()]) -> None:
            ...

        vals = {(1, "2", ())}
        """,
        errors=0,
    )


def test_argvals_check_against_correct_expression() -> None:
    _argvals_check_against_test_body(
        """
        def test_case(x: int, y: str, z: tuple[()]) -> None:
            ...

        vals = {(1, "2", ()): 4}.keys()
        """,
        errors=0,
    )


def test_argvals_check_against_correct_string() -> None:
    _argvals_check_against_test_body(
        """
        def test_case(c_1: str) -> None:
            ...

        vals = "abracadabra"
        """,
        errors=0,
    )


def test_argvals_check_against_incorrect_tuple() -> None:
    _argvals_check_against_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = ("a", "b", "c", "d")
        """,
        errors=4,
    )


def test_argvals_check_against_incorrect_string() -> None:
    _argvals_check_against_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = "abcd"
        """,
        errors=6,  # string error message spills onto 6 lines
    )


def test_argvals_check_against_incorrect_expression() -> None:
    _argvals_check_against_test_body(
        """
        def test_case(x_1: int) -> None:
            ...

        vals = [*[(), (1,), (2, 3,)], *[]]
        """,
        errors=1,
    )
