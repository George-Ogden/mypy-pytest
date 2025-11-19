from mypy.nodes import Decorator
from mypy.subtypes import is_same_type
import pytest

from .fixture import Fixture, FixtureParser
from .test_utils import check_error_messages, get_error_messages, parse


def _fixture_from_decorator_test_body(
    defs: str, is_fixture: bool, *, errors: list[str] | None = None, name: str = "fixture"
) -> None:
    parse_result = parse(defs)
    fixture_node = parse_result.defs[name]
    assert isinstance(fixture_node, Decorator)

    checker = parse_result.checker
    for def_ in parse_result.raw_defs:
        def_.accept(checker)

    fixture = Fixture.from_decorator(fixture_node, checker=checker)
    if is_fixture:
        assert fixture is not None
    else:
        assert fixture is None

    messages = get_error_messages(checker)
    check_error_messages(messages, errors=errors)


def test_fixture_from_decorator_no_decorator() -> None:
    _fixture_from_decorator_test_body(
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


def test_fixture_from_decorator_correct_decorator_no_args() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture() -> None:
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_decorator_correct_decorator_multiple_args() -> None:
    _fixture_from_decorator_test_body(
        """
        from pytest import fixture as fix

        @fix
        def fixture(x: int, y: bool) -> None:
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_decorator_correct_decorator_multiple_args_some_issues() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest

        @pytest.fixture()
        def fixture(pos: None, /, x: int, y: bool, z: type = str, *args: str, **kwargs: float) -> None:
            ...
        """,
        is_fixture=True,
        errors=["pos-only-arg", "opt-arg", "var-pos-arg", "var-kwarg"],
    )


def test_fixture_from_decorator_multiple_fixtures() -> None:
    _fixture_from_decorator_test_body(
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


def test_fixture_from_decorator_session_scope() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest

        @pytest.fixture(scope="session")
        def fixture(x: str) -> int:
            return 1
        """,
        is_fixture=True,
    )


def test_fixture_from_decorator_invalid_scope() -> None:
    with pytest.raises(TypeError):
        _fixture_from_decorator_test_body(
            """
            import pytest

            @pytest.fixture(scope="super")
            def fixture(x: str) -> None:
                ...
            """,
            is_fixture=True,
            errors=["invalid-fixture-scope"],
        )


def test_fixture_from_decorator_indirect_scope() -> None:
    _fixture_from_decorator_test_body(
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


def test_fixture_from_decorator_wrong_type_scope() -> None:
    _fixture_from_decorator_test_body(
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


def test_fixture_from_decorator_mark() -> None:
    _fixture_from_decorator_test_body(
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


def test_fixture_from_decorator_request_arg_wrong_type() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest
        from _pytest.fixtures import TopRequest

        @pytest.fixture
        def fixture(request: TopRequest) -> None:
            ...
        """,
        is_fixture=True,
        errors=["request-type"],
    )


def test_fixture_from_decorator_request_arg_correct_type() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest
        from _pytest.fixtures import SubRequest

        @pytest.fixture
        def fixture(request: SubRequest) -> None:
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_decorator_named_request() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest

        @pytest.fixture
        def request(request: None) -> None:
            ...
        """,
        is_fixture=False,
        errors=["request-keyword"],
        name="request",
    )


def test_fixture_from_decorator_partially_typed() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(x, y: str):
            ...
        """,
        is_fixture=True,
    )


def test_fixture_from_decorator_untyped() -> None:
    _fixture_from_decorator_test_body(
        """
        import pytest

        @pytest.fixture
        def fixture(x, y):
            ...
        """,
        is_fixture=True,
    )


def fixture_return_type_test_body(defs: str, is_generator: bool) -> None:
    parse_result = parse(defs)
    original_type = parse_result.types["original"]
    expected_type = parse_result.types["expected"]
    assert original_type is not None
    assert expected_type is not None

    assert is_same_type(
        FixtureParser.fixture_return_type(original_type, is_generator=is_generator),
        expected_type,
    )


def test_fixture_return_type_not_generator() -> None:
    fixture_return_type_test_body(
        """
        from typing import Generator

        original: Generator[int]
        expected: Generator[int]
        """,
        is_generator=False,
    )


def test_fixture_return_type_generator_one_arg() -> None:
    fixture_return_type_test_body(
        """
        from typing import Generator

        original: Generator[str]
        expected: str
        """,
        is_generator=True,
    )


def test_fixture_return_type_generator_multi_arg() -> None:
    fixture_return_type_test_body(
        """
        from typing import Generator, Literal

        original: Generator[Literal[0, 1], bool, int]
        expected: Literal[0, 1]
        """,
        is_generator=True,
    )


def test_fixture_return_type_iterable() -> None:
    fixture_return_type_test_body(
        """
        from typing import Iterable

        original: Iterable[str]
        expected: str
        """,
        is_generator=True,
    )


def test_fixture_return_type_iterator() -> None:
    fixture_return_type_test_body(
        """
        from typing import Iterator

        original: Iterator[None]
        expected: None
        """,
        is_generator=True,
    )


def test_fixture_return_type_sequence() -> None:
    fixture_return_type_test_body(
        """
        from typing import Sequence, Any

        original: Sequence[None]
        expected: Any
        """,
        is_generator=True,
    )
