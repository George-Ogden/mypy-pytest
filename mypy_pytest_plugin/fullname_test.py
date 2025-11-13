import pytest

from .fullname import Fullname


def _fullname_to_from_string_test_body(fullname: str, name: Fullname) -> None:
    assert Fullname.from_string(fullname) == name
    assert str(name) == fullname
    assert repr(name) == f"Fullname({fullname})"
    assert bool(name) == bool(fullname)


def test_fullname_to_from_string_empty() -> None:
    _fullname_to_from_string_test_body("", Fullname())


def test_fullname_to_from_string_single_part() -> None:
    _fullname_to_from_string_test_body("test_file", Fullname("test_file"))


def test_fullname_to_from_string_single_part_with_space() -> None:
    _fullname_to_from_string_test_body("function from class", Fullname("function from class"))


def test_fullname_to_from_string_multiple_parts() -> None:
    _fullname_to_from_string_test_body(
        "directory.sub_directory.conftest", Fullname("directory", "sub_directory", "conftest")
    )


def test_fullname_pop_back_empty() -> None:
    with pytest.raises(IndexError):
        Fullname().pop_back()


def test_fullname_pop_back_single() -> None:
    assert Fullname("file_name").pop_back() == ("file_name", Fullname())


def test_fullname_pop_back_multiple() -> None:
    assert Fullname("root", "folder_name", "test_file").pop_back() == (
        "test_file",
        Fullname("root", "folder_name"),
    )


def test_fullname_push_back_empty() -> None:
    assert Fullname().push_back("extra") == Fullname("extra")


def test_fullname_push_back_multiple() -> None:
    assert Fullname("root", "folder_name", "test_file").push_back("conftest") == Fullname(
        "root", "folder_name", "test_file", "conftest"
    )
