from typing import Union, Dict, List, Any, Tuple

from mypy_extensions import TypedDict

JSONType = Union[Dict[str, Any], List[Dict[str, Any]]]

IndexKeysDict = TypedDict("IndexKeysDict", {"columns": Tuple[str, ...], "unique": bool})
IndexesKeysType = List[IndexKeysDict]
IndexKeyType = Tuple[str, ...]
IndexType = TypedDict(
    "IndexType", {"index": Dict[Tuple[Any, ...], Any], "unique": bool}
)
IndexesType = Dict[IndexKeyType, IndexType]
