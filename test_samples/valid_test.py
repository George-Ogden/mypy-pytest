from typing import Literal
import pytest


@pytest.mark.parametrize("x", range(5))
@pytest.mark.parametrize(["y"], [(y,) for y in range(5)])
def test_valid(x: int, y: int) -> None:
    assert x + y == y + x


def pair() -> tuple[Literal[1], Literal[2]]:
    return 0, 2


@pytest.mark.parametrize("x, y", [(1, 2), pair()])
def test_internal_error(x: int, y: int) -> None:
    return x + y


@pytest.mark.skip
@pytest.mark.parametrize(argvalues="abcd", argnames="x")
def test_skipped_error(x: str) -> None:
    return x


def test_call_edge_cases() -> None:
    f_string = f"x{3}"
    list_addition = [1, 2, 3]
    list_addition += [4, 5, 6]


def test_iterable_sequence_builtin() -> None:
    l = [1, 2, 3, 4]
    t = tuple(l)
