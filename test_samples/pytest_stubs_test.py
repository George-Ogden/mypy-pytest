from typing import reveal_type

import pytest


reveal_type(pytest.param)()
reveal_type(pytest.param())
reveal_type(pytest.param(8))
reveal_type(pytest.param("a", None, 3.5))
reveal_type(
    pytest.param(
        lambda *args, **kwargs: ...,
        marks=[pytest.mark.skip, pytest.mark.notamark, pytest.mark.usefixtures()],
    )
)
