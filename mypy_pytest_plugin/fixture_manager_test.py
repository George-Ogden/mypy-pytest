from collections.abc import Sequence
from unittest import mock

from inline_snapshot import snapshot
from mypy.nodes import Decorator, FuncDef
from mypy.subtypes import is_same_type

from .fixture import Fixture
from .fixture_manager import FixtureManager
from .fullname import Fullname
from .test_argument import TestArgument
from .test_utils import parse_multiple, simple_module_lookup
from .utils import strict_cast, strict_not_none


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


def _fixture_manager_resolve_fixtures_test_body(
    modules: Sequence[tuple[str, str]],
    argnames: list[str],
    expected_fixtures: dict[str, list[str]],
) -> None:
    parse_result = parse_multiple(modules, header="import _pytest.fixtures\nimport typing")

    last_module_name, _ = modules[-1]
    fullname = f"{last_module_name}.test_request"

    checker = parse_result.checkers[last_module_name]
    fixture_def = parse_result.defs[fullname]
    assert isinstance(fixture_def, FuncDef)
    parse_result.checker_accept_all(checker)

    test_arguments = TestArgument.from_fn_def(fixture_def, checker=checker, source="test")
    assert test_arguments is not None

    with mock.patch.object(FixtureManager, "_module_lookup", simple_module_lookup):
        fixtures = FixtureManager(checker).resolve_fixtures(
            [test_argument.name for test_argument in test_arguments],
            argnames,
            Fullname.from_string(last_module_name),
        )

    assert not checker.errors.is_errors()
    assert {
        fixture_name: [str(fixture.fullname) for fixture in fixtures]
        for fixture_name, fixtures in fixtures.items()
    } == expected_fixtures


def test_fixture_manager_resolve_fixtures_no_requests() -> None:
    _fixture_manager_resolve_fixtures_test_body(
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
        {},
    )


def test_fixture_manager_resolve_fixtures_no_fixtures() -> None:
    _fixture_manager_resolve_fixtures_test_body(
        [
            (
                "file_test",
                """
                def test_request(x: int, y: str) -> None:
                    ...
                """,
            ),
        ],
        ["x", "y"],
        {},
    )


def test_fixture_manager_resolve_fixtures_single_request_same_file() -> None:
    _fixture_manager_resolve_fixtures_test_body(
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
        [],
        dict(fixture=["file_test.fixture", "conftest.fixture"]),
    )


def test_fixture_manager_resolve_fixtures_long_chain_same_file() -> None:
    _fixture_manager_resolve_fixtures_test_body(
        [
            (
                "file_test",
                """
                import pytest

                @pytest.fixture
                def fixture_3(fixture_4: None) -> None:
                    ...

                @pytest.fixture
                def fixture_2(fixture_3: None) -> None:
                    ...

                @pytest.fixture
                def fixture_1(fixture_2: None) -> None:
                    ...

                def test_request(fixture_1: None) -> None:
                    ...
                """,
            ),
        ],
        [],
        dict(
            fixture_1=["file_test.fixture_1"],
            fixture_2=["file_test.fixture_2"],
            fixture_3=["file_test.fixture_3"],
            fixture_4=[],
        ),
    )


def test_fixture_manager_resolve_fixtures_long_chain_masked_by_arg() -> None:
    _fixture_manager_resolve_fixtures_test_body(
        [
            (
                "conftest",
                """
                import pytest

                @pytest.fixture
                def fixture_4(fixture_5: None) -> None:
                    ...

                @pytest.fixture
                def fixture_3(fixture_4: None) -> None:
                    ...

                @pytest.fixture
                def fixture_2(fixture_3: None) -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                import pytest

                @pytest.fixture
                def fixture_3(fixture_4: None) -> None:
                    ...

                @pytest.fixture
                def fixture_2(fixture_3: None) -> None:
                    ...

                @pytest.fixture
                def fixture_1(fixture_2: None) -> None:
                    ...

                def test_request(fixture_1: None) -> None:
                    ...
                """,
            ),
        ],
        ["fixture_2"],
        dict(fixture_1=["file_test.fixture_1"]),
    )


def test_fixture_manager_resolve_fixtures_single_request_different_file() -> None:
    _fixture_manager_resolve_fixtures_test_body(
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
        [],
        dict(capsys=["folder.conftest.capsys", "conftest.capsys", "_pytest.capture.capsys"]),
    )


def test_fixture_manager_resolve_fixtures_request_builtins() -> None:
    _fixture_manager_resolve_fixtures_test_body(
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
        [],
        dict(capsys=["_pytest.capture.capsys"], snapshot=["pytest_snapshot.plugin.snapshot"]),
    )


def test_fixture_manager_resolve_inverted_request_graph() -> None:
    _fixture_manager_resolve_fixtures_test_body(
        [
            (
                "conftest",
                """
                import pytest

                @pytest.fixture
                def direct(indirect: None) -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                import pytest

                @pytest.fixture
                def indirect(argument: None) -> None:
                    ...

                def test_request(direct: None, argument: None) -> None:
                    ...
                """,
            ),
        ],
        [],
        dict(direct=["conftest.direct"], indirect=["file_test.indirect"]),
    )


def test_fixture_manager_resolve_fixtures_request_cycles() -> None:
    _fixture_manager_resolve_fixtures_test_body(
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
        [],
        dict(
            direct_cycle=["file_test.direct_cycle"],
            indirect_cycle_1=["file_test.indirect_cycle_1"],
            indirect_cycle_2=["file_test.indirect_cycle_2"],
            indirect_cycle_3=["file_test.indirect_cycle_3"],
        ),
    )


def test_fixture_manager_resolve_fixtures_autouse_fixtures() -> None:
    _fixture_manager_resolve_fixtures_test_body(
        [
            (
                "file_test",
                """
                import pytest
                from typing import Literal

                @pytest.fixture
                def requested_fixture() -> None:
                    ...

                @pytest.fixture(autouse=True)
                def automatic_fixture(requested_fixture: None, requested_arg: None) -> None:
                    ...

                @pytest.fixture(autouse=True)
                def automatic_fixture2() -> None:
                    ...

                @pytest.fixture
                def manual_fixture() -> None:
                    ...

                def test_request(manual_fixture: None) -> None:
                    ...

                __autouse__: Literal["automatic_fixture", "automatic_fixture2"]
                """,
            ),
        ],
        ["requested_arg"],
        dict(
            manual_fixture=["file_test.manual_fixture"],
            automatic_fixture=["file_test.automatic_fixture"],
            automatic_fixture2=["file_test.automatic_fixture2"],
            requested_fixture=["file_test.requested_fixture"],
        ),
    )


def test_fixture_manager_resolve_fixtures_autouse_fixture_ignored() -> None:
    _fixture_manager_resolve_fixtures_test_body(
        [
            (
                "conftest",
                """
                import pytest
                from typing import Literal

                @pytest.fixture
                def requested_fixture() -> None:
                    ...

                @pytest.fixture(autouse=True)
                def masked_automatic_fixture(requested_fixture: None) -> None:
                    ...

                __autouse__: Literal["masked_automatic_fixture"]
                """,
            ),
            (
                "file_test",
                """
                import pytest

                @pytest.fixture
                def masked_automatic_fixture() -> None:
                    ...

                def test_request(masked_automatic_fixture: None) -> None:
                    ...
                """,
            ),
        ],
        [],
        dict(
            masked_automatic_fixture=[
                "file_test.masked_automatic_fixture",
                "conftest.masked_automatic_fixture",
            ],
            requested_fixture=[
                "conftest.requested_fixture",
            ],
        ),
    )


def _fixture_manager_resolve_autouse_fixtures_test_body(
    modules: list[tuple[str, str]], expected_fixture_names: list[str]
) -> None:
    parse_result = parse_multiple(modules, header="import mypy_pytest_plugin_types")

    overrides = {}
    for module_name, module in parse_result.modules.items():
        checker = parse_result.checkers[module_name]
        parse_result.checker_accept_all(checker)
        autouse_node = module.names.pop(Fixture.AUTOUSE_NAME, None)
        for name, node in list(module.names.items()):
            if (
                isinstance(decorator := node.node, Decorator)
                and (fixture := Fixture.from_decorator(decorator, checker)) is not None
            ):
                overrides[(module_name, name)] = fixture.as_fixture_type(
                    decorator=decorator, checker=checker
                )
        if autouse_node is not None:
            assert is_same_type(
                strict_not_none(module.names[Fixture.AUTOUSE_NAME].type),
                strict_not_none(autouse_node.type),
            )
            module.names[Fixture.AUTOUSE_NAME] = autouse_node

    for (module_name, name), type_ in overrides.items():
        strict_cast(Decorator, checker.modules[module_name].names[name].node).var.type = type_

    fixtures = FixtureManager(checker).autouse_fixtures(Fullname.from_string(module_name))
    assert sorted(fixtures) == sorted(expected_fixture_names)


def test_fixture_manager_resolve_autouse_fixtures_none() -> None:
    _fixture_manager_resolve_autouse_fixtures_test_body([("file_test", "")], [])


def test_fixture_manager_resolve_autouse_fixtures_same_file() -> None:
    _fixture_manager_resolve_autouse_fixtures_test_body(
        [
            (
                "file_test",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["fixture"]

                @pytest.fixture(autouse=True)
                def fixture() -> None:
                    ...
                """,
            )
        ],
        ["fixture"],
    )


def test_fixture_manager_resolve_autouse_fixtures_conftest() -> None:
    _fixture_manager_resolve_autouse_fixtures_test_body(
        [
            (
                "conftest",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["conftest_fixture"]

                @pytest.fixture(autouse=True)
                def conftest_fixture() -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["file_fixture"]

                @pytest.fixture(autouse=True)
                def file_fixture() -> None:
                    ...
                """,
            ),
        ],
        ["conftest_fixture", "file_fixture"],
    )


def test_fixture_manager_resolve_autouse_fixtures_nested_conftest() -> None:
    _fixture_manager_resolve_autouse_fixtures_test_body(
        [
            (
                "conftest",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["conftest_fixture"]

                @pytest.fixture(autouse=True)
                def conftest_fixture() -> None:
                    ...
                """,
            ),
            (
                "nested.file_test",
                """
                import pytest
                from typing import Literal

                __autouse__: Literal["file_fixture1", "file_fixture2"]

                @pytest.fixture(autouse=True)
                def file_fixture1() -> None:
                    ...

                @pytest.fixture(autouse=True)
                def file_fixture2() -> None:
                    ...
                """,
            ),
        ],
        [
            "conftest_fixture",
            "file_fixture1",
            "file_fixture2",
        ],
    )


def test_fixture_manager_resolve_autouse_fixtures_conflicting_names() -> None:
    _fixture_manager_resolve_autouse_fixtures_test_body(
        [
            (
                "conftest",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["conftest_fixture", "fixture"]

                @pytest.fixture(autouse=True)
                def fixture() -> None:
                    ...

                @pytest.fixture(autouse=True)
                def conftest_fixture() -> None:
                    ...
                """,
            ),
            (
                "nested.conftest",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["conftest_fixture", "fixture"]

                @pytest.fixture(autouse=True)
                def fixture() -> None:
                    ...

                @pytest.fixture(autouse=True)
                def conftest_fixture() -> None:
                    ...
                """,
            ),
            (
                "nested.file_test",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["file_fixture", "fixture"]

                @pytest.fixture(autouse=True)
                def file_fixture() -> None:
                    ...

                @pytest.fixture(autouse=True)
                def fixture() -> None:
                    ...
                """,
            ),
        ],
        [
            "conftest_fixture",
            "file_fixture",
            "fixture",
        ],
    )


def test_fixture_manager_resolve_autouse_fixtures_builtin() -> None:
    _fixture_manager_resolve_autouse_fixtures_test_body(
        [
            (
                "_pytest.capture",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["capture_fixture"]

                @pytest.fixture(autouse=True)
                def capture_fixture() -> None:
                    ...
                """,
            ),
            (
                "file_test",
                """
                from typing import Literal
                import pytest

                __autouse__: Literal["fixture"]

                @pytest.fixture(autouse=True)
                def fixture() -> None:
                    ...
                """,
            ),
        ],
        [
            "capture_fixture",
            "fixture",
        ],
    )
