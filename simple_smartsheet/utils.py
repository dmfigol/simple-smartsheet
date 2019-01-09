import os

from marshmallow import EXCLUDE, RAISE


def get_unknown_field_handling(debug: bool) -> str:
    if debug:
        return RAISE
    else:
        return EXCLUDE


def is_debug() -> bool:
    debug_env_str = os.getenv("SIMPLE_SMARTSHEET_DEBUG", "").lower()
    return debug_env_str in ("yes", "true", "y", "1")
