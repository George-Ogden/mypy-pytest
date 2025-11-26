from collections.abc import Callable

from _pytest.fixtures import FixtureFunctionDefinition

class FixtureType[S: str, F: Callable, G: bool, N: str](FixtureFunctionDefinition): ...
