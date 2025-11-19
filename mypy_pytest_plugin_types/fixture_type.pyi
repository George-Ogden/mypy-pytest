from collections.abc import Callable

from _pytest.fixtures import FixtureFunctionDefinition

class FixtureType[S, F: Callable](FixtureFunctionDefinition): ...
