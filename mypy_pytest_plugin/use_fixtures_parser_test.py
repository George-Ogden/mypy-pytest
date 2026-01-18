from mypy.nodes import (
    CallExpr,
)
from mypy.subtypes import is_same_type
from mypy.types import LiteralType, UnionType

from .test_utils import (
    check_error_messages,
    get_error_messages,
    parse,
)
from .use_fixtures_parser import UseFixturesParser


def _inject_using_fixtures_mock_test_body(
    source: str, expected_fixture_names: list[str], *, errors: list[str] | None = None
) -> None:
    parse_result = parse(source, header="import mypy_pytest_plugin_types")
    parse_result.accept_all()
    checker = parse_result.checker

    usefixtures_call = parse_result.defs["call"]
    assert isinstance(usefixtures_call, CallExpr)

    type_ = UseFixturesParser.type_for_usefixtures(usefixtures_call, checker=checker)
    assert is_same_type(
        type_,
        checker.named_generic_type(
            "mypy_pytest_plugin_types._UsingFixturesMarkDecorator",
            [
                UnionType(
                    [
                        LiteralType(fixture_name, checker.named_type("builtins.str"))
                        for fixture_name in expected_fixture_names
                    ]
                )
            ],
        ),
    )

    check_error_messages(get_error_messages(checker), errors=errors)


def test_inject_fixture_using_fixtures_mock_no_arguments() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures()
        """,
        [],
    )


def test_inject_fixture_using_fixtures_mock_one_argument_valid() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture_name")
        """,
        ["fixture_name"],
    )


def test_inject_fixture_using_fixtures_mock_multiple_arguments_valid() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture_1", "fixture_2")
        """,
        ["fixture_1", "fixture_2"],
    )


def test_inject_fixture_using_fixtures_mock_one_argument_not_identifier() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture-1")
        """,
        [],
        errors=["invalid-usefixtures-name"],
    )


def test_inject_fixture_using_fixtures_mock_multiple_arguments_some_invalid() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("fixture-1", "fixture_2", "fixture.3")
        """,
        ["fixture_2"],
        errors=["invalid-usefixtures-name", "invalid-usefixtures-name"],
    )


def test_inject_fixture_using_fixtures_mock_multiple_arguments_keywords() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("is", "the", "def", "good", "?")
        """,
        ["the", "good"],
        errors=["invalid-usefixtures-name", "invalid-usefixtures-name", "invalid-usefixtures-name"],
    )


def test_inject_fixture_using_fixtures_mock_unreadable_fixture_name() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        string: str = "string"
        call = pytest.mark.usefixtures(string)
        """,
        [],
        errors=["unreadable-usefixtures-name"],
    )


def test_inject_fixture_using_fixtures_mock_request_argname() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest

        call = pytest.mark.usefixtures("request")
        """,
        [],
        errors=["request-keyword"],
    )


def test_parse_usefixtures_indirect_name() -> None:
    _inject_using_fixtures_mock_test_body(
        """
        import pytest
        from typing import Literal

        fixture_name: Literal["fixture"] = "fixture"

        call = pytest.mark.usefixtures(fixture_name)
        """,
        ["fixture"],
    )
