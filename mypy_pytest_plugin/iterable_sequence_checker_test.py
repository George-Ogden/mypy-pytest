from mypy.nodes import CallExpr

from .iterable_sequence_checker import IterableSequenceChecker
from .test_utils import check_error_messages, get_error_messages, parse


def _check_iterable_sequence_call_test_body(defs: str, *, errors: list[str] | None = None) -> None:
    parse_result = parse(defs)
    call = parse_result.defs["call"]
    assert isinstance(call, CallExpr)

    checker = parse_result.checker
    for def_ in parse_result.raw_defs:
        def_.accept(checker)

    assert not checker.errors.is_errors()

    IterableSequenceChecker(checker).check_iterable_sequence_call(call)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_check_iterable_sequence_no_args() -> None:
    _check_iterable_sequence_call_test_body(
        """
        def foo() -> int:
            return 0

        call = foo()
        """
    )


def test_check_iterable_sequence_one_arg_not_iterable() -> None:
    _check_iterable_sequence_call_test_body(
        """
        def foo(x: int) -> int:
            return 0

        call = foo(10)
        """
    )


def test_check_iterable_sequence_one_arg_both_iterable() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from typing import Iterable

        def foo(x: Iterable[int]) -> int:
            return 0

        call = foo(x=iter([12]))
        """
    )


def test_check_iterable_sequence_one_arg_both_sequence() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from collections.abc import Sequence

        def foo(x: Sequence[int]) -> int:
            return 0

        call = foo(x=[12])
        """
    )


def test_check_iterable_sequence_one_arg_iterable_sequence() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from collections.abc import Iterable, Sequence

        def foo(x: Iterable[int]) -> int:
            return 0

        call = foo(x=[12])
        """,
        errors=["iterable-sequence"],
    )


def test_check_iterable_sequence_many_args_iterable_sequence_mix() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from collections.abc import Iterable, Sequence

        def foo(x: Iterable[int], y: Iterable[float], *, z: Sequence[str]) -> int:
            return 0

        call = foo(iter([32]), z="abcd", y=[0.0, 1.0, 2.0])
        """,
        errors=["iterable-sequence"],
    )


def test_check_iterable_sequence_many_args_variadic_positional() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from typing import Iterable, Sequence

        def foo(x: Iterable[int], y: Iterable[float]) -> int:
            return 0

        pair: tuple[Sequence[int], Sequence[float]] = ([], [])

        call = foo(*pair)
        """
    )


def test_check_iterable_sequence_many_args_variadic_keyword() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from typing import Iterable, Literal, Sequence

        def foo(x: Iterable, y: Iterable) -> int:
            return 0

        map: dict[str, Sequence] = dict(x=[], y=[])

        call = foo(**map)
        """
    )


def test_check_iterable_sequence_default_argument() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from typing import Iterable

        def foo(x: Iterable = [1]) -> int:
            return 0

        call = foo()
        """
    )


def test_check_iterable_sequence_instance_method() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from typing import Iterable

        class Foo:
            def foo(self, it: Iterable) -> int:
                return 0

        call = Foo().foo([8])
        """,
        errors=["iterable-sequence"],
    )


def test_check_iterable_sequence_class_method() -> None:
    _check_iterable_sequence_call_test_body(
        """
        from typing import Iterable

        class Foo:
            @classmethod
            def foo(cls, it: Iterable) -> int:
                return 0

        call = Foo().foo([9])
        """,
        errors=["iterable-sequence"],
    )
