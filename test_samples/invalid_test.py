import pytest


@pytest.mark.skip
def test_missing_argname(arg: int) -> None: ...


@pytest.mark.skip
def test_missing_argname_with_error(x: int) -> None:
    return x


@pytest.mark.skip()
@pytest.mark.parametrize("y", range(4))
def test_wrong_argname_error(x: int) -> None: ...


@pytest.mark.parametrize(
    "foo, bar",
    [
        ([1], (1,)),
        ([2, 2], (2, 2)),
    ],
)
def test_invalid_type(foo: list[int], bar: tuple[int]) -> None: ...


def specific_test_case[T](x: T) -> tuple[T, T]:
    return [x, x]


@pytest.mark.parametrize(
    "x, y", (specific_test_case("a"), specific_test_case(2), specific_test_case(3.0))
)
def test_invalid_fn(x: int, y: int) -> None: ...
