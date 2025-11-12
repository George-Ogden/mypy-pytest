from typing import Iterable
import pytest


@pytest.mark.parametrize("unknown", [])
def test_ignored() -> None: ...


def iterable_sequence(x: Iterable) -> None: ...


iterable_sequence([1, 2, 3])
