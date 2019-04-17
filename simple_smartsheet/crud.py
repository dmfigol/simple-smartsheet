import logging
from typing import (
    TypeVar,
    Dict,
    Any,
    Generic,
    Optional,
    cast,
    Type,
    List,
    Iterator,
    TYPE_CHECKING,
    Sequence,
)


from simple_smartsheet import exceptions
from simple_smartsheet.models.base import CoreObject

if TYPE_CHECKING:
    from simple_smartsheet.smartsheet import Smartsheet  # noqa: F401
    from simple_smartsheet.models.extra import Result


logger = logging.getLogger(__name__)

TS = TypeVar("TS", bound=CoreObject)


# noinspection PyShadowingBuiltins
class CRUDRead(Generic[TS]):
    base_url = ""
    _get_url: Optional[str] = None
    _list_url: Optional[str] = None

    get_include_fields: Optional[Sequence[str]] = None
    get_exclude_fields: Sequence[str] = ()
    list_include_fields: Optional[Sequence[str]] = None
    list_exclude_fields: Sequence[str] = ()

    factory: Type[TS] = cast(Type[TS], CoreObject)

    def __init__(self, smartsheet: "Smartsheet") -> None:
        self.smartsheet = smartsheet

    def __iter__(self) -> Iterator[TS]:
        return iter(self.list())

    @property
    def get_url(self) -> str:
        return self._get_url or self.base_url + "/{id}"

    @property
    def list_url(self) -> str:
        return self._list_url or self.base_url

    def get_id(self, name: str) -> int:
        for obj in self.list():
            if obj._name == name:
                id_ = obj._id
                if id_ is None:
                    raise ValueError(
                        f"{self.factory.__qualname__} object with the name {name!r} "
                        f"does not have an id"
                    )
                return id_
        raise exceptions.SmartsheetObjectNotFound(
            f"{self.factory.__qualname__} object with the name {name!r} "
            f"has not been found"
        )

    def get(
        self, name: Optional[str] = None, id: Optional[int] = None, **kwargs: Any
    ) -> TS:
        """Fetches a CoreObject by name or id.

        Args:
            name: name of the object
            id: id of the object

        Returns:
            CoreObject
        """
        if id:
            endpoint = self.get_url.format(id=id)
            obj_data = cast(Dict[str, Any], self.smartsheet.get(endpoint, path=None))
            logger.debug(
                "Creating an object %s from data: %s",
                repr(self.factory.__qualname__),
                str(obj_data),
            )
            obj = self.factory.load(
                obj_data, self.get_include_fields, self.get_exclude_fields, **kwargs
            )
            if not obj.id:
                obj.id = id
            obj.smartsheet = self.smartsheet
            return obj
        elif name:
            id_ = self.get_id(name)
            return self.get(id=id_, **kwargs)
        raise ValueError(f"To use get method, either name or id must be provided")

    def list(self) -> List[TS]:
        """Fetches a list of CoreObject objects.

        Note: API usually returns an incomplete view of objects.
        For example: /sheets will return a list of sheets without columns or rows

        Returns:
            CoreObject
        """
        result = []
        for obj_data in self.smartsheet.get(
            self.list_url, params={"includeAll": "true"}
        ):
            logger.debug(
                "Creating an object '%s' from data: %s",
                self.factory.__qualname__,
                str(obj_data),
            )
            obj_data_ = cast(Dict[str, Any], obj_data)
            obj = self.factory.load(
                obj_data_, self.list_include_fields, self.list_exclude_fields
            )
            obj.smartsheet = self.smartsheet
            result.append(obj)
        return result


# noinspection PyShadowingBuiltins
class CRUD(CRUDRead[TS]):
    _update_url: Optional[str] = None
    _create_url: Optional[str] = None
    _delete_url: Optional[str] = None

    create_include_fields: Optional[Sequence[str]] = None
    create_exclude_fields: Sequence[str] = ()
    update_include_fields: Optional[Sequence[str]] = None
    update_exclude_fields: Sequence[str] = ()

    factory: Type[TS] = cast(Type[TS], CoreObject)

    @property
    def create_url(self) -> str:
        return self._create_url or self.base_url

    @property
    def update_url(self) -> str:
        return self._update_url or self.base_url + "/{id}"

    @property
    def delete_url(self) -> str:
        return self._delete_url or self.base_url + "/{id}"

    def create(self, obj: TS) -> "Result":
        """Creates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        obj.smartsheet = self.smartsheet
        endpoint = self.create_url.format(obj=obj)
        result = self.smartsheet.post(
            endpoint,
            obj.dump(
                only=self.create_include_fields, exclude=self.create_exclude_fields
            ),
        )
        return cast("Result", result)

    def update(self, obj: TS) -> "Result":
        """Updates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        obj.smartsheet = self.smartsheet
        endpoint = self.update_url.format(id=obj.id)
        result = self.smartsheet.put(
            endpoint,
            obj.dump(
                only=self.update_include_fields, exclude=self.update_exclude_fields
            ),
        )
        return cast("Result", result)

    def delete(self, name: Optional[str] = None, id: Optional[int] = None) -> "Result":
        """Deletes CoreObject by name or id

        Args:
            name: CoreObject name attribute
            id: CoreObject id attribute

        Returns:
            Result object
        """
        if id:
            endpoint = self.delete_url.format(id=id)
            return self.smartsheet.delete(endpoint)
        elif name:
            id_ = self.get_id(name)
            return self.delete(id=id_)
        raise ValueError(f"To use delete method, either name or id must be provided")
