import pytest


@pytest.fixture
def autouse_request() -> str:
    return "overridden"


@pytest.fixture(scope="package")
def request_autouse_fixture(autouse_request: int) -> None: ...


def test_autouse_fixtures() -> None: ...


@pytest.mark.skip
def test_direct_request_autouse_fixture(
    autouse_fixture: None, request_autouse_fixture: None
) -> None: ...


@pytest.mark.parametrize("autouse_request", [()])
def test_parametric_autouse() -> None: ...


@pytest.mark.skip
def test_late_autouse_request_pre(late_fixture: None) -> None: ...


@pytest.fixture(autouse=True)
def late_autouse_request(autouse_request: None) -> None: ...


@pytest.fixture
def late_fixture(normal_request: None) -> None: ...


@pytest.mark.skip
def test_late_autouse_request_post(late_fixture: None) -> None: ...
