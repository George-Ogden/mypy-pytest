from unittest import mock


class X:
    x: int

    def xx(self) -> None: ...


mock.patch.object(X(), "xx", lambda _: None)
mock.patch.object(X(), "xx", lambda: None)
mock.patch.object(X(), "x", 3)
mock.patch.object(X(), "x", "y")
mock.patch.object(X(), "x", mock.MagicMock())

with mock.patch("patch_object_test.X.xx", mock.Mock(return_value=None)) as m1:
    m1.assert_called()
with mock.patch("patch_object_test.X.xx", lambda self: None) as m2:
    m2.assert_called()


class Y:
    x: X


mock.patch.object(Y(), "x", X())
mock.patch.object(Y(), "x", mock.MagicMock())
mock.patch.object(Y(), "x", Y())


class PropertyClass:
    attr: int

    @property
    def prop(self) -> bool:
        return False


mock.patch.object(PropertyClass, "attr", 3)
mock.patch.object(PropertyClass, "attr", None)
mock.patch.object(PropertyClass, "prop", lambda: False)
mock.patch.object(PropertyClass, "prop", mock.PropertyMock(return_value="False"))
mock.patch.object(PropertyClass, "prop", mock.PropertyMock(return_value=True))
mock.patch.object(PropertyClass, "prop", mock.PropertyMock(lambda: False))
mock.patch.object(PropertyClass(), "prop", None)
mock.patch.object(PropertyClass(), "prop", False)
mock.patch.object(PropertyClass(), "prop", mock.PropertyMock(2.0))
mock.patch.object(PropertyClass(), "prop", mock.PropertyMock(False))


mock.patch.object(X(), "doesnotexist", mock.MagicMock())
