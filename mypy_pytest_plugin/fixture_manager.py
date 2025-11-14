from collections.abc import Iterable

from .fullname import Fullname


class FixtureManager:
    @classmethod
    def conftest_names(cls, name: Fullname) -> Iterable[Fullname]:
        while name:
            _, name = name.pop_back()
            yield name.push_back("conftest")
