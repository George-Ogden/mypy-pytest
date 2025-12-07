# Mypy Pytest

A Mypy plugin for type checking Pytest code.
(Not a Pytest plugin for running Mypy.)

## Features

- Check your parametrizations are correct
  - [x] You didn't mispel the argnames
  - [x] Your test cases have the right type
  - [x] You didn't forget any arguments
- Works with fixtures
  - [x] Your fixtures have the correct types
  - [x] All the fixture arguments are included
  - [x] You don't have conflicting fixtures
- Checks your mocks
  - [x] You're mocking something that exists
  - [x] Your mock has the correct type (or close enough)
- Checks your marks
  - [x] You're using a pre-defined mark
  - [x] Your mark is registered
- Checks for `Iterator` bugs
  - [x] You're robustly testing methods that want `Iterable` by giving them an `Iterable` and not a `Sequence`
- Works with whatever Pytest configuration
  - [x] Only checks your custom test files and test names
  - [x] Analyzes third-party Pytest plugins
- [x] Some [limitations](#limitations) because Mypy didn't expect plugins this cool :sunglasses:
- [x] All the rest of Mypy

## Install and Usage

Install with pip

```bash
pip install git+https://github.com/George-Ogden/mypy-pytest.git
```

Then register the plugin.

`pyproject.toml`:

```toml
plugins = ["mypy_pytest_plugin.plugin"]
```

`mypy.ini`:

```ini
plugins = mypy_pytest_plugin.plugin
```

See the [Mypy docs](https://mypy.readthedocs.io/en/stable/extending_mypy.html#configuring-mypy-to-use-plugins) for more info.

## Limitations

The Mypy plugin system is fairly limited.

This plugin only checks marked functions.
If you're using parametrized testing, that's fine as you `pytest.mark.parametrize`.
If not, [add a `typed` mark](https://docs.pytest.org/en/stable/how-to/mark.html#registering-marks) then mark any remaining tests you want to check.

```python
import random
import pytest

@pytest.fixture
def random_0_to_10() -> float:
    return random.random() * 10

@pytest.mark.typed
def test_random_string_length(random_0_to_10: int) -> None: # 'test_random_string_length' requests 'random_0_to_10' with type "float", but expects type "int"
    assert 0 <= random_0_to_10 <= 10
```

The order of the error messages is unclear, but this isn't an issue if you're using a plugin to your editor.

If you make changes to your Pytest config, Mypy will ignore this and give you a cached result.
If you want to see the newest version, clear the Mypy cache:

```bash
rm -rf .mypy_cache/
```

## Development

Use the GitHub issue tracker for bugs/feature requests.
