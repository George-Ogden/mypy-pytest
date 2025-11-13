from typing import Iterable
import pytest


@pytest.mark.parametrize("unknown", [])
def test_ignored() -> None: ...


def iterable_sequence(x: Iterable) -> None: ...


iterable_sequence([1, 2, 3])


@pytest.mark.parametrize("other", [])
def test_other() -> None: ...


test_other.__test__ = False
