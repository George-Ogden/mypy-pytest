import pytest
from _pytest.fixtures import SubRequest, TopRequest


@pytest.fixture
def bar(foo: int, request: TopRequest) -> int:
    return foo


@pytest.mark.parametrize("request", [1, 2, 3])
@pytest.mark.parametrize("foo", [1, 2, 3])
def test_request_names(bar: int, request: SubRequest) -> None: ...


@pytest.fixture
def request() -> None: ...
