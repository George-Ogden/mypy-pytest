import pytest


@pytest.mark.used_for_testing
def test_valid() -> None: ...


pytest.mark.not_a_mark

slow = pytest.mark.slow
skip = pytest.mark.skip


@slow
def test_slow(missed_arg: int) -> None: ...


@pytest.mark._bad_mark
def test_bad_mark(): ...
