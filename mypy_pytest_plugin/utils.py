from collections.abc import Callable, Hashable, Iterable
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


def identity[T](x: T) -> T:
    return x


@overload
def filter_unique[T: Hashable](it: Iterable[T], key: None = None) -> Iterable[T]: ...
@overload
def filter_unique[T, U: Hashable](it: Iterable[T], key: Callable[[T], U]) -> Iterable[T]: ...


@overload
def filter_unique[**P, R: Hashable](
    fn: Callable[P, Iterable[R]], /
) -> Callable[P, Iterable[R]]: ...


def filter_unique(it: Any, key: None | Callable[[Any], Any] = None) -> Any:
    if callable(it):
        return lambda *args, **kwargs: _filter_unique_iterator(it(*args, **kwargs), None)
    return _filter_unique_iterator(it, key)


def _filter_unique_iterator(it: Iterable[Any], key: None | Callable[[Any], Any]) -> Iterable[Any]:
    seen = set()
    if key is None:
        key = identity
    for element in it:
        value = key(element)
        if value not in seen:
            yield element
            seen.add(value)
