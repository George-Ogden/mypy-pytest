from .test_body_ranges import TestBodyRanges
from .test_utils import parse


def _test_body_ranges_test_body(defs: str, ranges: list[tuple[int, int]]) -> None:
    parse_result = parse(defs, header="")

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


def test_test_body_range_inclusion() -> None:
    test_body_ranges = TestBodyRanges.from_ranges(iter([(1, 2), (5, 7), (8, 8)]))
    for i, included in {
        0: False,
        1: True,
        2: True,
        3: False,
        4: False,
        5: True,
        6: True,
        7: True,
        8: True,
        9: False,
        10: False,
    }.items():
        assert (i in test_body_ranges) == included
