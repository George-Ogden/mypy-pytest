from typing import Literal
import pytest


@pytest.fixture
def defined_fixture() -> str:
    return "good fixture"


use = pytest.mark.usefixtures
missing_fixture: Literal["missing_fixture"] = "missing_fixture"


@use("missing_fixture")
def test_indirect_usefixture_call(defined_fixture: str) -> None: ...


@pytest.mark.usefixtures(missing_fixture)
def test_literal_fixture_context(defined_fixture: str) -> None: ...


@pytest.mark.usefixtures("defined_fixture")
def test_no_errors() -> None: ...


@pytest.mark.usefixtures("defined_fixture")
def test_invalid_type(defined_fixture: int) -> None: ...


@pytest.fixture
def indirect_fixture(argument: int) -> None: ...


@pytest.mark.usefixtures("indirect_fixture")
def test_indirect_fixture_unresolved() -> None: ...


@pytest.mark.usefixtures("indirect_fixture")
@pytest.mark.parametrize("argument", [1, 2, 3, 4.0])
def test_indirect_fixture_resolved() -> None: ...


@pytest.fixture
@pytest.mark.usefixtures()
@pytest.mark.usefixtures
def not_allowed() -> None: ...
