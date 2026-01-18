from mypy.nodes import (
    CallExpr,
    Decorator,
    FuncDef,
    MemberExpr,
)
from mypy.types import AnyType

from .test_utils import (
    check_error_messages,
    get_error_messages,
    parse,
)
from .use_fixtures_parser import UseFixturesParser
from .using_fixtures_parser import UsingFixturesParser


def _parse_usefixtures_test_body(
    defs: str, expected_fixture_names: list[str], *, errors: list[str] | None = None
) -> None:
    parse_result = parse(defs, header="import mypy_pytest_plugin_types")
    parse_result.accept_all()
    test_node = parse_result.defs["test_info"]
    assert isinstance(test_node, FuncDef | Decorator)
    checker = parse_result.checker

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=None)

    if isinstance(test_node, Decorator):
        for decorator in test_node.decorators:
            if (
                isinstance(decorator, CallExpr)
                and isinstance(decorator.callee, MemberExpr)
                and decorator.callee.name == "usefixtures"
            ):
                checker.store_type(
                    decorator,
                    UseFixturesParser.type_for_usefixtures(decorator, checker=checker),
                )

    arguments = UsingFixturesParser.use_fixture_requests(test_node, checker)
    assert {argument.name for argument in arguments} == set(expected_fixture_names)
    for argument in arguments:
        assert isinstance(argument.type_, AnyType)

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


def test_parse_usefixtures_no_decorators() -> None:
    _parse_usefixtures_test_body(
        """
        def test_info(x: str) -> None:
            ...
        """,
        [],
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


def test_parse_usefixtures_duplicated_name() -> None:
    _parse_usefixtures_test_body(
        """
        import pytest

        @pytest.mark.usefixtures("fixture_name", "fixture_name")
        def test_info(x: str) -> None:
            ...
        """,
        ["fixture_name"],
    )
