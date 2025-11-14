from collections.abc import Sequence

from inline_snapshot import snapshot
from mypy.nodes import FuncDef

from .fixture_manager import FixtureManager
from .fullname import Fullname
from .test_argument import TestArgument
from .test_utils import parse_multiple


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


def _fixture_manager_resolution_sequence_test_body(
    fullname: str, expected_fullnames: list[str]
) -> None:
    name = Fullname.from_string(fullname)
    expected = [Fullname.from_string(fullname) for fullname in expected_fullnames]
    assert list(FixtureManager.resolution_sequence(name)) == expected


def test_fixture_manager_resolution_sequence_empty() -> None:
    _fixture_manager_resolution_sequence_test_body("", [""])


def test_fixture_manager_resolution_sequence_file() -> None:
    _fixture_manager_resolution_sequence_test_body("file_test", ["file_test", "conftest", ""])


def test_fixture_manager_resolution_sequence_nested_folder() -> None:
    _fixture_manager_resolution_sequence_test_body(
        "folder.nested_test.file_test",
        [
            "folder.nested_test.file_test",
            "folder.nested_test.conftest",
            "folder.conftest",
            "conftest",
            "",
        ],
    )


def test_fixture_manager_default_fixture_module_names() -> None:
    modules = FixtureManager.default_fixture_module_names()
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


def _fixture_manager_resolve_requests_and_fixtures_test_body(
    modules: Sequence[tuple[str, str]],
    expected_request_names: Sequence[str],
    expected_fixture_fullnames: Sequence[str],
) -> None:
    parse_result = parse_multiple(modules)

    last_module_name, _ = modules[-1]
    fullname = f"{last_module_name}.test_request"

    checker = parse_result.checkers[last_module_name]
    fixture_def = parse_result.defs[fullname]
    assert isinstance(fixture_def, FuncDef)
    for def_ in parse_result.raw_defs:
        def_.accept(checker)

    start = TestArgument.from_fn_def(fixture_def, checker=checker)
    assert start is not None
    requests, fixtures = FixtureManager(checker).resolve_requests_and_fixtures(
        start, Fullname.from_string(last_module_name)
    )

    assert not checker.errors.is_errors()
    assert sorted(requests.keys()) == sorted(expected_request_names)
    assert sorted(str(fixture.fullname) for fixture in fixtures) == sorted(
        fullname for fullname in expected_fixture_fullnames
    )


def test_fixture_manager_resolve_requests_no_requests() -> None:
    _fixture_manager_resolve_requests_and_fixtures_test_body(
        [
            (
                "conftest",
                """
                import pytest

                @pytest.fixture
                def fixture() -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                def test_request() -> None:
                    ...
                """,
            ),
        ],
        [],
        [],
    )


def test_fixture_manager_resolve_requests_single_request_same_file() -> None:
    _fixture_manager_resolve_requests_and_fixtures_test_body(
        [
            (
                "conftest",
                """
                import pytest

                @pytest.fixture
                def fixture() -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                import pytest

                @pytest.fixture
                def fixture() -> None:
                    ...

                def test_request(fixture: None) -> None:
                    ...
                """,
            ),
        ],
        ["fixture"],
        ["file_test.fixture"],
    )


def test_fixture_manager_resolve_requests_single_request_different_file() -> None:
    _fixture_manager_resolve_requests_and_fixtures_test_body(
        [
            (
                "_pytest.capture",
                """
                import pytest

                @pytest.fixture
                def capsys() -> None:
                    ...
                """,
            ),
            (
                "conftest",
                """
                import pytest

                @pytest.fixture
                def capsys() -> None:
                    ...
                """,
            ),
            (
                "folder.conftest",
                """
                import pytest

                @pytest.fixture
                def capsys() -> None:
                    ...
                """,
            ),
            (
                "folder.file_test",
                """
                def test_request(capsys: None) -> None:
                    ...
                """,
            ),
        ],
        ["capsys"],
        ["folder.conftest.capsys"],
    )


def test_fixture_manager_resolve_requests_request_builtins() -> None:
    _fixture_manager_resolve_requests_and_fixtures_test_body(
        [
            (
                "pytest_snapshot.plugin",
                """
                import pytest

                @pytest.fixture
                def snapshot() -> None:
                    ...
                """,
            ),
            (
                "_pytest.capture",
                """
                import pytest

                @pytest.fixture
                def capsys() -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                from typing import Any

                def test_request(capsys: Any, snapshot: Any) -> None:
                    ...
                """,
            ),
        ],
        ["capsys", "snapshot"],
        ["_pytest.capture.capsys", "pytest_snapshot.plugin.snapshot"],
    )


def test_fixture_manager_resolve_requests_complex_graph() -> None:
    _fixture_manager_resolve_requests_and_fixtures_test_body(
        [
            (
                "conftest",
                """
                from typing import Any
                import pytest

                @pytest.fixture
                def local() -> str:
                    return ""

                @pytest.fixture
                def non_local() -> int:
                    return 1

                @pytest.fixture
                def indirect_non_local(non_local: int) -> int:
                    return non_local

                @pytest.fixture
                def inverted_local() -> bool:
                    return False

                @pytest.fixture
                def indirect_inverted_local(inverted_local) -> bool:
                    return inverted_local
                """,
            ),
            (
                "file_test",
                """
                import pytest

                @pytest.fixture
                def local() -> str:
                    return ""

                @pytest.fixture
                def non_local() -> int:
                    return 1

                @pytest.fixture
                def indirect_local(local: str) -> str:
                    return local

                @pytest.fixture
                def inverted_local() -> bool:
                    return True

                def test_request(
                    indirect_local: str,
                    indirect_non_local: int,
                    indirect_inverted_local: bool,
                    inverted_local: bool,
                ) -> None:
                    ...
                """,
            ),
        ],
        [
            "indirect_local",
            "local",
            "indirect_non_local",
            "non_local",
            "inverted_local",
            "indirect_inverted_local",
        ],
        [
            "file_test.indirect_local",
            "file_test.local",
            "file_test.inverted_local",
            "conftest.indirect_inverted_local",
            "conftest.indirect_non_local",
            "conftest.non_local",
        ],
    )


def test_fixture_manager_resolve_requests_request_cycles() -> None:
    _fixture_manager_resolve_requests_and_fixtures_test_body(
        [
            (
                "file_test",
                """
                from typing import Any
                import pytest

                @pytest.fixture
                def direct_cycle(direct_cycle: None) -> None:
                    ...

                @pytest.fixture
                def indirect_cycle_1(indirect_cycle_2: None) -> None:
                    ...

                @pytest.fixture
                def indirect_cycle_2(indirect_cycle_3: None) -> None:
                    ...

                @pytest.fixture
                def indirect_cycle_3(indirect_cycle_1: None) -> None:
                    ...

                def test_request(direct_cycle: None, indirect_cycle_1: None) -> None:
                    ...
                """,
            ),
        ],
        ["direct_cycle", "indirect_cycle_1", "indirect_cycle_2", "indirect_cycle_3"],
        [
            "file_test.direct_cycle",
            "file_test.indirect_cycle_1",
            "file_test.indirect_cycle_2",
            "file_test.indirect_cycle_3",
        ],
    )
