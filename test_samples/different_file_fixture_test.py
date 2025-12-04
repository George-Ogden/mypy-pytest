from typing import Literal
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


@pytest.fixture
def ordered_fixture1(ordered_fixture2: None) -> Literal[2]:
    return 2


@pytest.fixture
def ordered_fixture2(ordered_fixture1: None) -> Literal[3]:
    return 3


@pytest.mark.skip
def test_ordered_case1(ordered_fixture1: None, ordered_fixture2: None) -> None: ...


@pytest.mark.skip
def test_ordered_case2(ordered_fixture2: None, ordered_fixture1: None) -> None: ...
