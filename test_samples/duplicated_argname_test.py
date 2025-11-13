import pytest


@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("x", [-1, -2, -3])
def test_x(x: int) -> None: ...
