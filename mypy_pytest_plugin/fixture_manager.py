from collections.abc import Iterable

from .fullname import Fullname


class FixtureManager:
    @classmethod
    def conftest_names(cls, name: Fullname) -> Iterable[Fullname]:
        while name:
            _, name = name.pop_back()
            yield name.push_back("conftest")

    @classmethod
    def full_resolution_sequence(cls, name: Fullname) -> Iterable[Fullname]:
        yield name
        yield from cls.conftest_names(name)
        if name:
            yield Fullname()
