from typing import Literal
import pytest


@pytest.fixture
def base_int_fixture() -> int:
    return 0


@pytest.fixture
def indirect_int_fixture(base_int_fixture: int) -> int:
    return base_int_fixture + 1


def missed_fixture_decorator_in_another_file() -> int:
    return 0


@pytest.fixture
def fixture_with_missing_argument(missing_argument: None) -> None: ...


@pytest.fixture(autouse=True, scope="module")
def autouse_request() -> None: ...


@pytest.fixture(autouse=True, scope="module")
def autouse_fixture(autouse_request: None) -> None: ...


@pytest.fixture
def ordered_fixture1() -> Literal[0]:
    return 0


@pytest.fixture
def ordered_fixture2() -> Literal[1]:
    return 1


pytest_plugins = "pytester"
