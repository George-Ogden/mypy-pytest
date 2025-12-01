import pytest


@pytest.fixture(scope="class")
def base_int_fixture() -> str:
    return ""


@pytest.mark.skip
def test_valid_indirect_int_fixture(indirect_int_fixture: int) -> None: ...


@pytest.mark.skip
def test_invalid_indirect_int_fixture(indirect_int_fixture: int, base_int_fixture: str) -> None: ...


@pytest.mark.skip
def test_requests_fixture_with_missing_argument(fixture_with_missing_argument: None) -> None: ...


@pytest.mark.parametrize("", [])
def test_missed_fixture_decorator_in_another_file(
    missed_fixture_decorator_in_another_file: None,
) -> None: ...
