import os

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
        "env_var_value,expected,",
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
    def test_is_debug(self, env_var_value, expected):
        env_var = "SIMPLE_SMARTSHEET_DEV"
        os.environ[env_var] = env_var_value
        assert utils.is_development() == expected
