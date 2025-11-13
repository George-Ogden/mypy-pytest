from typing import Callable
import pytest


@pytest.mark.parametrize("unknown", [])
def ignored() -> None: ...


def wrap(x: Callable) -> None: ...


@pytest.mark.parametrize("x", [])
def test_x(x): ...
