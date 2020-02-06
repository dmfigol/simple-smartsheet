import os
import types

import pytest

from simple_smartsheet import utils


class TestEnvVars:
    @pytest.mark.parametrize(
        "env_var_value,expected",
        [
            ("yes", True),
            ("Yes", True),
            ("True", True),
            ("true", True),
            ("1", True),
            ("0", False),
            ("", False),
            ("false", False),
            ("False", False),
        ],
    )
    def test_is_env_var(self, env_var_value, expected):
        env_var = "TEST_VAR"
        os.environ[env_var] = env_var_value
        assert utils.is_env_var(env_var) == expected


@pytest.mark.parametrize(
    "data,n,expected",
    [
        (["a", "b", "c", "d", "e"], 1, [("a",), ("b",), ("c",), ("d",), ("e",)]),
        (["a", "b", "c", "d", "e"], 2, [("a", "b"), ("c", "d"), ("e",)]),
        (["a", "b", "c", "d", "e"], 3, [("a", "b", "c"), ("d", "e")]),
        (["a", "b", "c", "d", "e"], 4, [("a", "b", "c", "d"), ("e",)]),
        (["a", "b", "c", "d", "e"], 5, [("a", "b", "c", "d", "e")]),
        (["a", "b", "c", "d", "e"], 6, [("a", "b", "c", "d", "e")]),
    ],
)
def test_grouper(data, n, expected):
    assert isinstance(utils.grouper(data, n), types.GeneratorType)
    assert list(utils.grouper(data, n)) == expected
