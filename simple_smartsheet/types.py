from typing import Union, Dict, List, Any, Tuple, DefaultDict, TYPE_CHECKING

from mypy_extensions import TypedDict

if TYPE_CHECKING:
    from simple_smartsheet.models import Row

JSONType = Union[Dict[str, Any], List[Dict[str, Any]]]

IndexKeysType = TypedDict("IndexKeysType", {"columns": Tuple[str, ...], "unique": bool})
IndexesKeysType = List[IndexKeysType]
IndexesType = DefaultDict[Tuple[str, ...], Dict[Tuple, Union["Row", List["Row"]]]]
