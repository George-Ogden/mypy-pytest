from collections.abc import Callable


def compose[S, T, U](f: Callable[[T], U], g: Callable[[S], T]) -> Callable[[S], U]:
    return lambda x: f(g(x))
