import pytest


@pytest.fixture
def base_int_fixture() -> int:
    return 0


@pytest.fixture
def indirect_int_fixture(base_int_fixture: int) -> int:
    return base_int_fixture + 1


@pytest.fixture
@pytest.mark.skip
def fixture_and_mark() -> None: ...
