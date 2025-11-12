from typing import Any


class Testable:
    def __init__(self, *args: Any, **kwargs: Any) -> None: ...

    __test__: bool
