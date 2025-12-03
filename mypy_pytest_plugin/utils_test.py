import pytest

from .utils import extract_singleton, strict_cast, strict_not_none


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
