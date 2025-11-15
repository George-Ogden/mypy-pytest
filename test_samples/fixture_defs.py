from typing import Iterable, Literal, Sequence, cast
import pytest


@pytest.mark.fixture
@pytest.mark.fixture
def not_a_fixture() -> None: ...


@pytest.fixture
def basic_fixture() -> None: ...


@pytest.fixture(scope="module")
def non_trivial_fixture(foo: int, bar: Iterable) -> Sequence: ...


@pytest.fixture()
@pytest.fixture
def double_fixture(foo: int, bar: Iterable) -> int:
    return foo


@pytest.fixture(scope="unknown")
def wrong_scope_fixture() -> str:
    return ""


@pytest.fixture(scope=cast(Literal["module", "session"], "module"))
def invalid_scope_fixture() -> str:
    return ""


@pytest.mark.skip
@pytest.fixture
def fixture_and_mark[T](argument: T) -> T:
    return argument
