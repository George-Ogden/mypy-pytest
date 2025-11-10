from src.plugin import PytestPlugin


def plugin(version: str) -> type[PytestPlugin]:
    return PytestPlugin
