import logging
from typing import (
    TypeVar,
    Dict,
    Any,
    Generic,
    Optional,
    cast,
    Type,
    Union,
    List,
    TYPE_CHECKING,
    Sequence,
)


from simple_smartsheet import exceptions
from simple_smartsheet.models.base import CoreObject

if TYPE_CHECKING:
    from simple_smartsheet.smartsheet import Smartsheet, AsyncSmartsheet  # noqa: F401
    from simple_smartsheet.models.extra import Result


logger = logging.getLogger(__name__)

TS = TypeVar("TS", bound=CoreObject)


class CRUDAttrs:
    base_url = ""
    _get_url: Optional[str] = None
    _list_url: Optional[str] = None

    get_include_fields: Optional[Sequence[str]] = None
    get_exclude_fields: Sequence[str] = ()
    list_include_fields: Optional[Sequence[str]] = None
    list_exclude_fields: Sequence[str] = ()

    _update_url: Optional[str] = None
    _create_url: Optional[str] = None
    _delete_url: Optional[str] = None

    create_include_fields: Optional[Sequence[str]] = None
    create_exclude_fields: Sequence[str] = ()
    update_include_fields: Optional[Sequence[str]] = None
    update_exclude_fields: Sequence[str] = ()


class CRUDBase(CRUDAttrs, Generic[TS]):
    factory: Type[TS] = cast(Type[TS], CoreObject)

    def __init__(self, smartsheet: Union["Smartsheet", "AsyncSmartsheet"]) -> None:
        self.smartsheet = smartsheet

    @property
    def get_url(self) -> str:
        return self._get_url or self.base_url + "/{id}"

    @property
    def list_url(self) -> str:
        return self._list_url or self.base_url

    @property
    def create_url(self) -> str:
        return self._create_url or self.base_url

    @property
    def update_url(self) -> str:
        return self._update_url or self.base_url + "/{id}"

    @property
    def delete_url(self) -> str:
        return self._delete_url or self.base_url + "/{id}"


# noinspection PyShadowingBuiltins
class CRUDReadBase(CRUDBase[TS]):
    def _get_id(self, name: str, objects: List[TS]) -> int:
        for obj in objects:
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

    def _create_obj_from_data(self, data: Dict[str, Any]) -> TS:
        logger.debug(
            "Creating an object %s from data: %s",
            repr(self.factory.__qualname__),
            str(data),
        )
        obj = self.factory.load(data, self.get_include_fields, self.get_exclude_fields)
        obj.smartsheet = self.smartsheet
        return obj

    def _create_objects_from_data(self, data: List[Dict[str, Any]]) -> List[TS]:
        result: List[TS] = []
        for obj_data in data:
            logger.debug(
                "Creating an object '%s' from data: %s",
                self.factory.__qualname__,
                str(obj_data),
            )
            obj = self.factory.load(
                obj_data, self.list_include_fields, self.list_exclude_fields
            )
            obj.smartsheet = self.smartsheet
            result.append(obj)
        return result


# noinspection PyShadowingBuiltins
class CRUDRead(CRUDReadBase[TS]):
    smartsheet: "Smartsheet"

    def get_id(self, name: str) -> int:
        objects = self.list()
        return self._get_id(name, objects)

    def get(self, name: Optional[str] = None, id: Optional[int] = None) -> TS:
        """Fetches a CoreObject by name or id.

        Args:
            name: name of the object
            id: id of the object

        Returns:
            CoreObject
        """
        if id:
            endpoint = self.get_url.format(id=id)
            smartsheet = self.smartsheet
            obj_data = cast(Dict[str, Any], smartsheet.get(endpoint, path=None))
            return self._create_obj_from_data(obj_data)
        elif name:
            id_ = self.get_id(name)
            return self.get(id=id_)
        raise ValueError(f"To use get method, either name or id must be provided")

    def list(self) -> List[TS]:
        """Fetches a list of CoreObject objects.

        Note: API usually returns an incomplete view of objects.
        For example: /sheets will return a list of sheets without columns or rows

        Returns:
            CoreObject
        """
        smartsheet = self.smartsheet
        objects_data = cast(
            List[Dict[str, Any]],
            smartsheet.get(self.list_url, params={"includeAll": "true"}),
        )
        return self._create_objects_from_data(objects_data)


# noinspection PyShadowingBuiltins
class CRUD(CRUDRead[TS]):
    def create(self, obj: TS) -> "Result":
        """Creates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        smartsheet = self.smartsheet
        obj.smartsheet = smartsheet
        endpoint = self.create_url.format(obj=obj)
        obj_data = obj.dump(
            only=self.create_include_fields, exclude=self.create_exclude_fields
        )
        result = smartsheet.post(endpoint, obj_data)
        return cast("Result", result)

    def update(self, obj: TS) -> "Result":
        """Updates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        smartsheet = self.smartsheet
        obj.smartsheet = smartsheet
        endpoint = self.update_url.format(id=obj.id)
        obj_data = obj.dump(
            only=self.update_include_fields, exclude=self.update_exclude_fields
        )
        result = smartsheet.put(endpoint, obj_data)
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
            smartsheet = self.smartsheet
            return smartsheet.delete(endpoint)
        elif name:
            id_ = self.get_id(name)
            return self.delete(id=id_)
        raise ValueError(f"To use delete method, either name or id must be provided")


class AsyncCRUDRead(CRUDReadBase[TS]):
    smartsheet: "AsyncSmartsheet"

    async def get_id(self, name: str) -> int:
        objects = await self.list()
        return self._get_id(name, objects)

    async def get(self, name: Optional[str] = None, id: Optional[int] = None) -> TS:
        """Fetches a CoreObject by name or id.

        Args:
            name: name of the object
            id: id of the object

        Returns:
            CoreObject
        """
        if id:
            endpoint = self.get_url.format(id=id)
            smartsheet = self.smartsheet
            data = cast(Dict[str, Any], await smartsheet.get(endpoint, path=None))
            return self._create_obj_from_data(data)
        elif name:
            id_ = await self.get_id(name)
            return await self.get(id=id_)
        raise ValueError(f"To use get method, either name or id must be provided")

    async def list(self) -> List[TS]:
        """Fetches a list of CoreObject objects.

        Note: API usually returns an incomplete view of objects.
        For example: /sheets will return a list of sheets without columns or rows

        Returns:
            CoreObject
        """
        smartsheet = self.smartsheet
        data = await smartsheet.get(self.list_url, params={"includeAll": "true"})
        return self._create_objects_from_data(cast(List[Dict[str, Any]], data))


class AsyncCRUD(AsyncCRUDRead[TS]):
    async def create(self, obj: TS) -> "Result":
        """Creates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        smartsheet = self.smartsheet
        obj.smartsheet = smartsheet
        endpoint = self.create_url.format(obj=obj)
        obj_data = obj.dump(
            only=self.create_include_fields, exclude=self.create_exclude_fields
        )
        result = await smartsheet.post(endpoint, obj_data)
        return cast("Result", result)

    async def update(self, obj: TS) -> "Result":
        """Updates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        smartsheet = self.smartsheet
        obj.smartsheet = smartsheet
        endpoint = self.update_url.format(id=obj.id)
        obj_data = obj.dump(
            only=self.update_include_fields, exclude=self.update_exclude_fields
        )
        result = await smartsheet.put(endpoint, obj_data)
        return cast("Result", result)

    async def delete(
        self, name: Optional[str] = None, id: Optional[int] = None
    ) -> "Result":
        """Deletes CoreObject by name or id

        Args:
            name: CoreObject name attribute
            id: CoreObject id attribute

        Returns:
            Result object
        """
        if id:
            endpoint = self.delete_url.format(id=id)
            smartsheet = self.smartsheet
            return await smartsheet.delete(endpoint)
        elif name:
            id_ = await self.get_id(name)
            return await self.delete(id=id_)
        raise ValueError(f"To use delete method, either name or id must be provided")
