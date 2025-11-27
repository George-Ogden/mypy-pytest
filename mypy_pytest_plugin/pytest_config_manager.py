import functools

import _pytest.config
from pytest import Config, Session  # noqa: PT013


class PytestConfigManager:
    @classmethod
    @functools.cache
    def session(cls) -> Session:
        config = _pytest.config.get_config()
        config.parse(["-s", "--noconftest"])
        return Session.from_config(config)

    @classmethod
    def config(cls) -> Config:
        return cls.session().config

    @classmethod
    @functools.cache
    def file_patterns(cls) -> list[str]:
        return cls.config().getini("python_files")

    @classmethod
    @functools.cache
    def fn_patterns(cls) -> list[str]:
        return cls.config().getini("python_functions")

    @classmethod
    @functools.cache
    def markers(cls) -> list[str]:
        return cls.config().getini("markers")
