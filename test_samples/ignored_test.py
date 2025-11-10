import pytest


@pytest.mark.parametrize("unknown", [])
def ignored() -> None: ...
