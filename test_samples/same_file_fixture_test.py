from typing import Literal
import pytest


@pytest.fixture
def int_fixture() -> int:
    return 0


@pytest.fixture
def bool_fixture() -> bool:
    return True


@pytest.mark.skip
def test_valid_fixture(int_fixture: int, bool_fixture: bool) -> None: ...


@pytest.mark.skip
def test_invalid_fixture_type(int_fixture: int, bool_fixture: Literal[True]) -> None: ...


@pytest.fixture
def indirect_bool_fixture_invalid(bool_fixture: Literal[False]) -> bool:
    return not bool_fixture


@pytest.mark.skip
def test_indirect_bool_fixture_invalid(indirect_bool_fixture_invalid: bool) -> None: ...


@pytest.mark.parametrize("bool_fixture", [True, False])
def test_indirect_bool_fixture_invalid_shadowing(
    indirect_bool_fixture_invalid: bool, bool_fixture: Literal[True]
) -> None:
    return bool_fixture == indirect_bool_fixture_invalid


@pytest.mark.parametrize("bool_fixture", [False])
@pytest.mark.parametrize("indirect_bool_fixture_invalid", [True, False])
def test_indirect_bool_fixture_invalid_extra_arg(indirect_bool_fixture_invalid: bool) -> None: ...
