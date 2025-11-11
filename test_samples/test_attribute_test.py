import pytest


@pytest.mark.parametrize("x", [])
def test_true_test_attribute(x: bool) -> None: ...


test_true_test_attribute.__test__ = True


@pytest.mark.slow
def test_false_test_attribute_1(x: bool) -> None: ...


@pytest.mark.slow
def test_false_test_attribute_2(x: int) -> None: ...


test_false_test_attribute_1.__test__ = test_false_test_attribute_2.__test__ = False
