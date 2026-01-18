import itertools

from mypy.nodes import CallExpr, Decorator, FuncDef, RefExpr
from mypy.types import AnyType

from .test_info import TestInfo
from .test_utils import (
    check_error_messages,
    get_error_messages,
    parse,
)
from .use_fixtures_parser import UseFixturesParser


def _usefixtures_parse_fixture_names_test_body(
    source: str, expected_fixture_names: list[str], *, errors: list[str] | None = None
) -> None:
    parse_result = parse(source, header="import mypy_pytest_plugin_types")
    parse_result.accept_all()
    checker = parse_result.checker

    usefixtures_call = parse_result.defs["call"]
    assert isinstance(usefixtures_call, CallExpr)
    assert isinstance(usefixtures_call.callee, RefExpr)
    usefixtures_call.callee.fullname = "_pytest.mark.usefixtures"

    requests = UseFixturesParser.use_fixture_requests([usefixtures_call], checker=checker)
    assert {request.name for request in requests} == set(expected_fixture_names)

    check_error_messages(get_error_messages(checker), errors=errors)


def test_usefixtures_parse_fixture_names_no_arguments() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures()
        """,
        [],
    )


def test_usefixtures_parse_fixture_names_one_argument_valid() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture_name")
        """,
        ["fixture_name"],
    )


def test_usefixtures_parse_fixture_names_multiple_arguments_valid() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture_1", "fixture_2")
        """,
        ["fixture_1", "fixture_2"],
    )


def test_usefixtures_parse_fixture_names_one_argument_not_identifier() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture-1")
        """,
        [],
        errors=["invalid-usefixtures-name"],
    )


def test_usefixtures_parse_fixture_names_multiple_arguments_some_invalid() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture-1", "fixture_2", "fixture.3")
        """,
        ["fixture_2"],
        errors=["invalid-usefixtures-name", "invalid-usefixtures-name"],
    )


def test_usefixtures_parse_fixture_names_multiple_arguments_keywords() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("is", "the", "def", "good", "?")
        """,
        ["the", "good"],
        errors=["invalid-usefixtures-name", "invalid-usefixtures-name", "invalid-usefixtures-name"],
    )


def test_usefixtures_parse_fixture_names_unreadable_fixture_name() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        string: str = "string"
        call = pytest.mark.usefixtures(string)
        """,
        [],
        errors=["unreadable-usefixtures-name"],
    )


def test_usefixtures_parse_fixture_names_request_argname() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("request")
        """,
        [],
        errors=["request-keyword"],
    )


def test_parse_usefixtures_indirect_name() -> None:
    _usefixtures_parse_fixture_names_test_body(
        """
        import pytest
        from typing import Literal

        fixture_name: Literal["fixture"] = "fixture"

        call = pytest.mark.usefixtures(fixture_name)
        """,
        ["fixture"],
    )


def _parse_usefixtures_test_body(
    defs: str, expected_fixture_names: list[str], *, errors: list[str] | None = None
) -> None:
    parse_result = parse(defs, header="import mypy_pytest_plugin_types")
    parse_result.accept_all()
    test_node = parse_result.defs["test_info"]
    assert isinstance(test_node, Decorator)
    checker = parse_result.checker

    check_error_messages(get_error_messages(checker), errors=None)

    requests = UseFixturesParser.use_fixture_requests(test_node.decorators, checker)
    assert {request.name for request in requests} == set(expected_fixture_names)
    for request in requests:
        assert isinstance(request.type_, AnyType)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_parse_usefixtures_one_fixture() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures(
            "fixture_name"
        )
        def test_info(x: str) -> None:
            ...
        """,
        ["fixture_name"],
    )


def test_parse_usefixtures_no_usefixture_decorators() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.skip
        def test_info(x: str) -> None:
            ...
        """,
        [],
    )


def test_parse_usefixtures_no_fixtures() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures()
        def test_info(x: str) -> None:
            ...
        """,
        [],
    )


def test_parse_usefixtures_multiple_fixtures() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures(
            "fixture1", "fixture2", "fixture3"
        )
        def test_info(x: str) -> None:
            ...
        """,
        ["fixture1", "fixture2", "fixture3"],
    )


def test_parse_usefixtures_multiple_decorators() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures()
        @pytest.mark.usefixtures(
            "fixture1"
        )
        @pytest.mark.usefixtures(
            "fixture_a", "fixture_b"
        )
        def test_info(x: str) -> None:
            ...
        """,
        ["fixture1", "fixture_a", "fixture_b"],
    )


def test_parse_usefixtures_invalid_identifier() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures("not a var")
        @pytest.mark.usefixtures("okay")
        def test_info(x: str) -> None:
            ...
        """,
        ["okay"],
        errors=["invalid-usefixtures-name"],
    )


def _test_info_with_usefixtures_test_body(
    defs: str,
    expected_argument_names: list[str],
    expected_fixture_names: list[str],
    *,
    errors: list[str] | None = None,
) -> None:
    parse_result = parse(defs, header="import mypy_pytest_plugin_types")
    parse_result.accept_all()
    test_node = parse_result.defs["test_info"]
    assert isinstance(test_node, FuncDef | Decorator)
    checker = parse_result.checker

    check_error_messages(get_error_messages(checker), errors=None)

    test_info = TestInfo.from_fn_def(test_node, checker=checker)
    assert test_info is not None
    assert {request.name for request in test_info.requests} == set(
        itertools.chain(expected_argument_names, expected_fixture_names)
    )
    for request in test_info.requests:
        if request.name in expected_argument_names:
            assert not isinstance(request.type_, AnyType)
        elif request.name in expected_fixture_names:
            assert isinstance(request.type_, AnyType)

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_test_info_with_usefixtures_duplicated_name() -> None:
    _test_info_with_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures("fixture_name", "fixture_name")
        def test_info(x: str) -> None:
            ...
        """,
        ["x"],
        ["fixture_name"],
    )


def test_test_info_with_usefixtures_test_arg_name_and_usefixture_name() -> None:
    _test_info_with_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures("fixture_name", "another_name")
        def test_info(x: str, fixture_name: None) -> None:
            ...
        """,
        ["x", "fixture_name"],
        ["another_name"],
    )


def test_test_info_with_usefixtures_no_fixtures() -> None:
    _test_info_with_usefixtures_test_body(
        """
        import pytest

        def test_info(x: str, fixture_name: None) -> None:
            ...
        """,
        ["x", "fixture_name"],
        [],
    )
