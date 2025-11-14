from inline_snapshot import snapshot

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


def _fixture_manager_full_resolution_sequence_test_body(
    fullname: str, expected_fullnames: list[str]
) -> None:
    name = Fullname.from_string(fullname)
    expected = [Fullname.from_string(fullname) for fullname in expected_fullnames]
    assert list(FixtureManager.full_resolution_sequence(name)) == expected


def test_fixture_manager_full_resolution_sequence_empty() -> None:
    _fixture_manager_full_resolution_sequence_test_body("", [""])


def test_fixture_manager_full_resolution_sequence_file() -> None:
    _fixture_manager_full_resolution_sequence_test_body("file_test", ["file_test", "conftest", ""])


def test_fixture_manager_full_resolution_sequence_nested_folder() -> None:
    _fixture_manager_full_resolution_sequence_test_body(
        "folder.nested_test.file_test",
        [
            "folder.nested_test.file_test",
            "folder.nested_test.conftest",
            "folder.conftest",
            "conftest",
            "",
        ],
    )


def test_fixture_manager_default_fixture_modules() -> None:
    modules = FixtureManager.default_fixture_modules()
    assert sorted(map(str, modules)) == snapshot(
        [
            "_pytest.cacheprovider",
            "_pytest.capture",
            "_pytest.doctest",
            "_pytest.fixtures",
            "_pytest.junitxml",
            "_pytest.logging",
            "_pytest.monkeypatch",
            "_pytest.recwarn",
            "_pytest.subtests",
            "_pytest.tmpdir",
            "inline_snapshot.pytest_plugin",
            "pytest_snapshot.plugin",
            "xdist.plugin",
        ]
    )
