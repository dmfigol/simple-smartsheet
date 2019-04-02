import os
from typing import Optional, Sequence, Any

from marshmallow import EXCLUDE, RAISE


def get_unknown_field_handling(debug: bool) -> str:
    if debug:
        return RAISE
    else:
        return EXCLUDE


def is_env_var(env_var: str) -> bool:
    env_var_str = os.getenv(env_var, "").lower()
    return env_var_str in ("yes", "true", "y", "1")


def is_debug() -> bool:
    return is_env_var("SIMPLE_SMARTSHEET_DEBUG")


def create_repr(obj: Any, attrs: Optional[Sequence[str]] = None):
    if attrs is None:
        attrs = obj.__dict__.keys()
    attrs_repr = ", ".join(f"{attr}={getattr(obj, attr)!r}" for attr in attrs)
    return f"{obj.__class__.__qualname__}({attrs_repr})"
