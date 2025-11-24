from unittest import mock

from .fixture_manager import FixtureManager
from .test_utils import (
    parse,
    simple_module_lookup,
    test_info_from_defs,
)


def _test_info_prune_active_requests_and_fixtures_test_body(
    defs: str, arguments: list[str], expected_requests: list[str], expected_fixtures: list[str]
) -> None:
    test_info = test_info_from_defs(defs, name="test_info")
    parse_result = parse(defs)
    parse_result.accept_all()

    with mock.patch.object(FixtureManager, "_module_lookup", simple_module_lookup):
        _ = test_info.request_graph

    for argument in arguments:
        test_info._available_requests[argument].used = True

    active_requests, active_fixtures = test_info.request_graph._prune_active_nodes_and_fixtures()
    assert active_requests.keys() == set(expected_requests)
    assert active_fixtures.keys() == set(expected_fixtures)


def test_info_prune_active_requests_and_fixtures_no_fixtures_no_arguments() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        def test_info() -> None:
            ...

        """,
        [],
        [],
        [],
    )


def test_info_prune_active_requests_and_fixtures_no_fixtures_arguments_all_used() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        def test_info(x: int, y: bool) -> None:
            ...

        """,
        ["x", "y"],
        ["x", "y"],
        [],
    )


def test_info_prune_active_requests_and_fixtures_no_fixtures_arguments_some_used() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        def test_info(x: int, y: bool, z: str) -> None:
            ...
        """,
        ["x", "z"],
        ["x", "y", "z"],
        [],
    )


def test_info_prune_active_requests_and_fixtures_indirect_fixture_directly_used() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def indirect() -> bool:
            return False

        @pytest.fixture
        def direct(indirect: bool) -> bool:
            return not indirect

        def test_info(direct: bool) -> None:
            ...
        """,
        ["direct"],
        ["direct"],
        [],
    )


def test_info_prune_active_requests_and_fixtures_indirect_fixture_indirectly_used() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def indirect() -> bool:
            return False

        @pytest.fixture
        def direct(indirect: bool) -> bool:
            return not indirect

        def test_info(direct: bool) -> None:
            ...
        """,
        ["indirect"],
        ["direct", "indirect"],
        ["direct"],
    )


def test_info_prune_active_requests_and_fixtures_indirect_fixture_default_used() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def indirect() -> bool:
            return False

        @pytest.fixture
        def direct(indirect: bool) -> bool:
            return not indirect

        def test_info(direct: bool) -> None:
            ...
        """,
        [],
        ["direct", "indirect"],
        ["direct", "indirect"],
    )


def test_info_prune_active_requests_and_fixtures_unused_indirect_fixture() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def indirect(missing_argument: bool) -> bool:
            return not missing_argument

        @pytest.fixture
        def direct(indirect: bool) -> bool:
            return not indirect

        def test_info(direct: bool) -> None:
            ...
        """,
        [],
        ["direct", "indirect", "missing_argument"],
        ["direct", "indirect"],
    )


def test_info_prune_active_requests_and_fixtures_partially_unresolved_graph() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def another_missing(extra_missing: int) -> int:
            return -extra_missing

        @pytest.fixture
        def missing_fixture(another_missing: int, another_included: int) -> bool:
            return another_missing > another_included

        @pytest.fixture
        def multi_argument(missing_fixture: bool, included_argument: bool) -> bool:
            return missing_fixture and included_argument

        def test_info(multi_argument: bool) -> None:
            ...
        """,
        ["included_argument", "another_included"],
        [
            "multi_argument",
            "missing_fixture",
            "included_argument",
            "another_missing",
            "another_included",
            "extra_missing",
        ],
        ["another_missing", "multi_argument", "missing_fixture"],
    )


def test_info_prune_active_requests_and_fixtures_cycle() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def cycle_2(cycle_1: int) -> int:
            return cycle_1 + 1

        @pytest.fixture
        def cycle_1(cycle_2: int) -> int:
            return cycle_2 + 1

        def test_info(cycle_1: int) -> None:
            ...
        """,
        [],
        [
            "cycle_1",
            "cycle_2",
        ],
        ["cycle_1", "cycle_2"],
    )


def test_info_prune_active_requests_and_fixtures_partially_flattened() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def deep_fixture(arg: None) -> None:
            ...

        @pytest.fixture
        def shallow_fixture(deep_fixture: None) -> None:
            ...

        def test_info(shallow_fixture: None, deep_fixture: None, arg: None) -> None:
            ...
        """,
        ["shallow_fixture"],
        ["shallow_fixture", "arg", "deep_fixture"],
        ["deep_fixture"],
    )


def test_info_prune_active_requests_and_fixtures_flattened() -> None:
    _test_info_prune_active_requests_and_fixtures_test_body(
        """
        import pytest

        @pytest.fixture
        def deep_fixture(arg: None) -> None:
            ...

        @pytest.fixture
        def shallow_fixture(deep_fixture: None) -> None:
            ...

        def test_info(shallow_fixture: None, deep_fixture: None, arg: None) -> None:
            ...
        """,
        ["shallow_fixture", "deep_fixture", "arg"],
        ["shallow_fixture", "deep_fixture", "arg"],
        [],
    )
