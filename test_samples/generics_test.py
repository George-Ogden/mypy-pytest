from typing import SupportsInt
import pytest


@pytest.mark.parametrize("x", [8, "str", ()])
def test_identity[T](x: T) -> T:
    return x


@pytest.mark.parametrize("x, y", [(8, 8), ("a", "b"), ((), ())])
def test_multiple_generics[T](x: T, y: T) -> T:
    return x


@pytest.mark.parametrize("x", [8, "a", ()])
@pytest.mark.parametrize("y", [4, "b", ()])
def test_multiple_split_generics[T](x: T, y: T) -> T:
    return x


@pytest.mark.parametrize("x, y", [(8, 8), ("a", "b"), ((), ()), (1.0, 2.0)])
def test_bounded_generics[T: SupportsInt](x: T, y: T) -> T:
    return x
