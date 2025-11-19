import pytest


@pytest.fixture(scope="class")
def base_int_fixture() -> str:
    return ""


@pytest.mark.skip
def test_valid_indirect_int_fixture(indirect_int_fixture: int) -> None: ...


@pytest.mark.skip
def test_invalid_indirect_int_fixture(indirect_int_fixture: int, base_int_fixture: str) -> None: ...
