from unittest import mock


class X:
    x: int

    def xx(self) -> None: ...


mock.patch.object(X(), "xx", lambda _: None)
mock.patch.object(X(), "xx", lambda: None)
mock.patch.object(X(), "x", 3)
mock.patch.object(X(), "x", "y")
mock.patch.object(X(), "x", mock.MagicMock())


class Y:
    x: X


mock.patch.object(Y(), "x", X())
mock.patch.object(Y(), "x", mock.MagicMock())
mock.patch.object(Y(), "x", Y())
