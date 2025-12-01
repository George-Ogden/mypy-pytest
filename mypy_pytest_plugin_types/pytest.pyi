from collections.abc import Collection

from _pytest.mark import ParameterSet as PytestParameterSet
from _pytest.mark import _HiddenParam
from pytest import Mark, MarkDecorator  # noqa: PT013

class ParameterSet[*Ts](PytestParameterSet): ...

def param[*Ts](
    *values: *Ts,
    marks: MarkDecorator | Collection[MarkDecorator | Mark] = (),
    id: str | _HiddenParam | None = None,
) -> ParameterSet[*Ts]: ...
