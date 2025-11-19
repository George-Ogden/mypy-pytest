import pytest


@pytest.mark.parametrize("x", [None])
def test_higher_conftest(x: None, y: str, base_int_fixture: int) -> None: ...
