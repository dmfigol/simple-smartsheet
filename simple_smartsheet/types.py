from typing import Union, Dict, List, Any, Tuple, DefaultDict, TYPE_CHECKING

from mypy_extensions import TypedDict

if TYPE_CHECKING:
    from simple_smartsheet.models import Row  # noqa

JSONType = Union[Dict[str, Any], List[Dict[str, Any]]]

IndexKeysDict = TypedDict("IndexKeysDict", {"columns": Tuple[str, ...], "unique": bool})
IndexesKeysType = List[IndexKeysDict]
IndexesType = DefaultDict[
    Tuple[str, ...], Dict[Tuple[Any, ...], Union["Row", List["Row"]]]
]
