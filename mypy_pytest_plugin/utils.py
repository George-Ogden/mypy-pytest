from collections.abc import Callable, Iterable
from typing import Any, overload


def compose[S, T, U](f: Callable[[T], U], g: Callable[[S], T]) -> Callable[[S], U]:
    return lambda x: f(g(x))


@overload
def strict_cast[T](type: type[T], expr: Any, /) -> T: ...


@overload
def strict_cast(type: object, expr: Any, /) -> Any: ...


def strict_cast(type: object, expr: Any, /) -> Any:
    try:
        type_checks = isinstance(expr, type)  # type: ignore
    except TypeError:
        ...
    else:
        if not type_checks:
            raise TypeError()
    return expr


def strict_not_none[T](expr: T | None, /) -> T:
    if expr is None:
        raise TypeError()
    return expr


def extract_singleton[T](singleton: Iterable[T], /) -> T:
    [value] = singleton
    return value
