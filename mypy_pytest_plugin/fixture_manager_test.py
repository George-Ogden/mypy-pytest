from .fixture_manager import FixtureManager
from .fullname import Fullname


def _fixture_manager_conftest_names_test_body(fullname: str, expected_fullnames: list[str]) -> None:
    name = Fullname.from_string(fullname)
    expected = [Fullname.from_string(fullname) for fullname in expected_fullnames]
    assert list(FixtureManager.conftest_names(name)) == expected


def test_fixture_manager_conftest_names_empty() -> None:
    _fixture_manager_conftest_names_test_body("", [])


def test_fixture_manager_conftest_names_file() -> None:
    _fixture_manager_conftest_names_test_body("file_test", ["conftest"])


def test_fixture_manager_conftest_names_nested_folder() -> None:
    _fixture_manager_conftest_names_test_body(
        "folder.nested_test.file_test",
        ["folder.nested_test.conftest", "folder.conftest", "conftest"],
    )
