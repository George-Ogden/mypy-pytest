from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
import itertools
from typing import Any

import pytest

from .utils import cache_by_id, extract_singleton, filter_unique, strict_cast, strict_not_none


def test_strict_cast_type() -> None:
    x: int | None = 5
    y: int = strict_cast(int, x)
    assert y == 5


def test_strict_cast_union() -> None:
    x: int | str | None = 5
    y: int | str = strict_cast(int | str, x)
    assert y == 5


def test_strict_cast_fail() -> None:
    x: int | str | None = 5
    with pytest.raises(TypeError):
        _: str | None = strict_cast(str | None, x)


def test_extract_singleton_no_items() -> None:
    with pytest.raises(ValueError):
        extract_singleton(iter([]))


def test_extract_singleton_one_item() -> None:
    assert extract_singleton(iter([()])) == ()


def test_extract_singleton_two_items() -> None:
    with pytest.raises(ValueError):
        extract_singleton(iter({1, 2}))


def test_strict_not_none_not_none() -> None:
    x: int | None = 5
    y: int = strict_not_none(x)
    assert y == 5


def test_strict_not_none_is_none() -> None:
    x: int | None = None
    with pytest.raises(TypeError):
        _: int = strict_not_none(x)


@pytest.mark.parametrize(
    "it, key, expected",
    [
        # empty
        ([], None, []),
        # already unique
        (range(10), None, list(range(10))),
        # already with key
        (range(10), lambda n: n + 1, list(range(10))),
        # unique unless key
        (range(10), lambda n: n // 2, range(0, 10, 2)),
        # non unique
        ([1, 2, 3, 3, 2, 5, 1, 3, 0], None, [1, 2, 3, 5, 0]),
        # non unique with key
        ([1, 2, -2, -3, -4, 4, 0, -1, 3], lambda x: abs(x), [1, 2, -3, -4, 0]),
        # infinite unique
        (itertools.count(), None, list(range(10))),
        # infinite not unique
        (itertools.count(), lambda n: n // 3, list(range(0, 20, 3))),
    ],
)
def test_unique_iterator(
    it: Iterable, key: Callable[[Any], Any] | None, expected: Sequence
) -> None:
    assert list(itertools.islice(filter_unique(it, key=key), len(expected))) == list(expected)


@filter_unique
def count_to_n_twice(n: int) -> Iterable[int]:
    for i in range(n):
        yield i
        yield i


@pytest.mark.parametrize("n", range(5))
def test_unique_wrapper(n: int) -> None:
    assert list(count_to_n_twice(n)) == list(range(n))


def test_cache_by_id() -> None:
    id = 0

    @cache_by_id
    def foo(*args: Any) -> int:
        nonlocal id
        return (id := id + 1)

    assert foo() == foo()
    assert foo(None) == foo(None)

    @dataclass(unsafe_hash=True)
    class IntWrapper:
        x: int

    a = IntWrapper(0)
    b = IntWrapper(0)
    foo_a = foo(a)
    foo_b = foo(b)
    assert foo_a != foo_b

    a.x += 1
    b.x += 1

    assert foo(a) == foo_a
    assert foo(b) == foo_b
