import pytest


@pytest.mark.parametrize("x", [])
def test_true_test_attribute(x: bool) -> None: ...


test_true_test_attribute.__test__ = True
