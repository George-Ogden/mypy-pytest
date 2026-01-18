from typing import Any, Callable, Generator, Iterable, Sequence, cast
import pytest


@pytest.mark.skip
def test_missing_argname(arg: int) -> None: ...


@pytest.mark.skip
def test_missing_argname_with_error(x: int) -> str:
    return x


@pytest.mark.skip()
@pytest.mark.parametrize("y", range(4))
def test_wrong_argname_error(x: int) -> Any: ...


@pytest.mark.parametrize("foo, bar", [([1], (1,)), ([2, 2], (2, 2))])
def test_invalid_type(foo: list[int], bar: tuple[int]) -> None: ...


def specific_test_case[T](x: T) -> tuple[T, T]:
    return [x, x]


@pytest.mark.parametrize(
    "x, y", (specific_test_case("a"), specific_test_case(2), specific_test_case(3.0))
)
def test_invalid_fn(x: int, y: int) -> None: ...


def iterable_sequence(it: Iterable, seq: Sequence) -> None: ...


class IterableSequenceTester:
    def iterable_sequence(self, seq: Sequence[int], it: Iterable[int]) -> None: ...


def test_iterable_sequence() -> None:
    iterable_sequence([1], [2])
    IterableSequenceTester().iterable_sequence([3], [4])


def no_test_iterable_sequence() -> None:
    iterable_sequence([5], [6])
    IterableSequenceTester().iterable_sequence([7], [8])


def wrap(x: Callable) -> None: ...


@wrap
@pytest.mark.parametrize("x", [])
def test_x(x): ...


@pytest.mark.parametrize("", [pytest.param(())])
@pytest.mark.parametrize(
    "x",
    [
        pytest.param("1", foo="bar"),
        pytest.param(cast(int, 2), marks=[pytest.mark.skip, pytest.mark.usefixtures("fixtures")]),
    ],
)
@pytest.mark.parametrize(
    "y, z", [pytest.param("3", 4), pytest.param(*(5.0, "6.0")), pytest.param(*("7.0", 8.0))]
)
def test_pytest_param(x: int, y: float, z: str) -> None: ...
