from typing import Iterable
import pytest


@pytest.fixture
def yield_fixture() -> Iterable[int]:
    yield 3


@pytest.fixture
def no_yield_fixture() -> Iterable[int]:
    return iter([3])


@pytest.mark.skip
def test_generators(
    yield_fixture: int,
    no_yield_fixture: int,
) -> None: ...


@pytest.mark.skip
def test_no_generators(
    yield_fixture: Iterable[int],
    no_yield_fixture: Iterable[int],
) -> None: ...
