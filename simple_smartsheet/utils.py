import os
from itertools import islice
from typing import Optional, Sequence, Any, List, Iterable, Tuple, Type, TypeVar

import marshmallow


def get_unknown_field_handling(strict_validation: bool) -> str:
    if strict_validation:
        return marshmallow.RAISE
    else:
        return marshmallow.EXCLUDE


def is_env_var(env_var: str) -> bool:
    env_var_str = os.getenv(env_var, "").lower()
    return env_var_str in ("yes", "true", "y", "1")


def create_repr(obj: Any, attrs: Optional[Sequence[str]] = None):
    if attrs is None:
        attrs = obj.__dict__.keys()
    attrs_kv: List[str] = []
    for attr in attrs:
        attr_value = getattr(obj, attr)
        if attr_value is not None:
            attrs_kv.append(f"{attr}={attr_value!r}")
    attrs_repr = ", ".join(attrs_kv)
    return f"{obj.__class__.__qualname__}({attrs_repr})"


G = TypeVar("G")


def grouper(
    iterable: Iterable[G], n: int, cast: Type[Any] = tuple
) -> Iterable[Tuple[G, ...]]:
    it = iter(iterable)
    while True:
        chunk = cast(islice(it, n))
        if not chunk:
            return
        yield chunk
