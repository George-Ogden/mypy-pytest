from .test_body_ranges import TestBodyRanges
from .test_utils import parse


def _test_body_ranges_test_body(defs: str, ranges: list[tuple[int, int]]) -> None:
    parse_result = parse(defs)

    test_body_ranges = TestBodyRanges.from_defs(parse_result.raw_defs)

    assert test_body_ranges == TestBodyRanges.from_ranges(ranges)


def test_test_body_ranges_no_fns() -> None:
    _test_body_ranges_test_body(
        """
        import typing

        class Foo:
            def test_foo(self) -> None: ...

        test_bar = 3
        """,
        [],
    )


def test_test_body_ranges_mixed_fns() -> None:
    _test_body_ranges_test_body(
        """
        def test_bar() -> None:
            ...

        def bar_test() -> None:
            ...

        def nested() -> None:
            def test_inner() -> None:
                ...

        def test_multiline() -> None:


            ...

        def test_inline() -> None: ...

        import pytest

        @pytest.mark.parametrize(
            "x", [3, 4, 5]
        )
        def test_decorator(x: int) -> None:
            x += 0
            x *= 1
        """,
        [(1, 2), (11, 14), (16, 16), (23, 25)],
    )
