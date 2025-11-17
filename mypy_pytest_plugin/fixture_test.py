from mypy.nodes import Decorator
import pytest

from .fixture import Fixture
from .test_utils import check_error_codes, parse


def _fixture_from_defs_test_body(
    defs: str, is_fixture: bool, *, errors: list[str] | None = None
) -> None:
    parse_result = parse(defs)
    fixture_node = parse_result.defs["fixture"]
    assert isinstance(fixture_node, Decorator)

    checker = parse_result.checker
    for def_ in parse_result.raw_defs:
        def_.accept(checker)

    fixture = Fixture.from_decorator(fixture_node, checker=checker)
    if is_fixture:
        assert fixture is not None
    else:
        assert fixture is None

    check_error_codes(errors)


def test_fixture_from_fn_defs_no_decorator() -> None:
    _fixture_from_defs_test_body(
        """
        from typing import Callable

        def wrap(x: Callable) -> None:
            ...

        @wrap
        def fixture() -> None:
            ...
        """,
        is_fixture=False,
    )


def test_fixture_from_fn_defs_correct_decorator_no_args() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture() -> None:
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_fn_defs_correct_decorator_multiple_args() -> None:
    _fixture_from_defs_test_body(
        """
        from pytest import fixture as fix

        @fix
        def fixture(x: int, y: bool) -> None:
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_fn_defs_correct_decorator_multiple_args_some_issues() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest

        @pytest.fixture()
        def fixture(pos: None, /, x: int, y: bool, z: type = str, *args: str, **kwargs: float) -> None:
            ...
        """,
        is_fixture=True,
        errors=["pos-only-arg", "opt-arg", "var-pos-arg", "var-kwarg"],
    )


def test_fixture_from_fn_defs_multiple_fixtures() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest

        @pytest.fixture()
        @pytest.fixture
        @pytest.fixture
        def fixture() -> None:
            ...
        """,
        is_fixture=False,
        errors=["duplicate-fixture", "duplicate-fixture"],
    )


def test_fixture_from_fn_defs_session_scope() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest

        @pytest.fixture(scope="session")
        def fixture(x: str) -> int:
            return 1
        """,
        is_fixture=True,
    )


def test_fixture_from_fn_defs_invalid_scope() -> None:
    with pytest.raises(TypeError):
        _fixture_from_defs_test_body(
            """
            import pytest

            @pytest.fixture(scope="super")
            def fixture(x: str) -> None:
                ...
            """,
            is_fixture=True,
            errors=["invalid-fixture-scope"],
        )


def test_fixture_from_fn_defs_indirect_scope() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest
        from typing import Literal

        scope: Literal["module"] = "module"

        @pytest.fixture(scope=scope)
        def fixture(x: str) -> None:
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_fn_defs_wrong_type_scope() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest
        from typing import Literal

        scope: Literal["module", "session"] = "module"

        @pytest.fixture(scope=scope)
        def fixture(x: str) -> None:
            ...
        """,
        is_fixture=True,
        errors=["invalid-fixture-scope"],
    )


def test_fixture_from_fn_defs_mark() -> None:
    _fixture_from_defs_test_body(
        """
        import pytest

        skipper = pytest.mark.skip

        @pytest.fixture
        @skipper
        @pytest.mark.slow
        def fixture(x: str) -> None:
            ...
        """,
        is_fixture=False,
        errors=["marked-fixture", "marked-fixture"],
    )
