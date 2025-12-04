from typing import Any
import pytest


@pytest.fixture
def direct_cycle(direct_cycle: None) -> None: ...


@pytest.fixture
def indirect_cycle_1(indirect_cycle_2: None) -> None: ...


@pytest.fixture
def indirect_cycle_2(indirect_cycle_3: None) -> None: ...


@pytest.fixture
def indirect_cycle_3(indirect_cycle_1: None) -> None: ...


@pytest.fixture
def base_int_fixture(base_int_fixture: None) -> int:
    return 1


@pytest.mark.skip
def test_request(direct_cycle: None, indirect_cycle_1: None, base_int_fixture: int) -> None: ...
