import logging
import copy
from datetime import datetime
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
    Union,
    ClassVar,
    Sequence,
)


import attr
import marshmallow
from cattr.converters import Converter

from simple_smartsheet import utils
from simple_smartsheet import config
from simple_smartsheet.types import IndexesType, IndexKeysType

if TYPE_CHECKING:
    from simple_smartsheet.smartsheet import Smartsheet  # noqa: F401
    from simple_smartsheet.models.extra import Result


logger = logging.getLogger(__name__)

converter = Converter()
converter.register_structure_hook(datetime, lambda ts, _: ts)
converter.register_structure_hook(IndexKeysType, lambda x, _: x)
converter.register_structure_hook(IndexesType, lambda x, _: x)
converter.register_structure_hook(Union[float, str, datetime, None], lambda ts, _: ts)


class Schema(marshmallow.Schema):
    class Meta:
        unknown = utils.get_unknown_field_handling(config.DEBUG)

    @marshmallow.post_dump
    def remove_none(self, data):
        return {key: value for key, value in data.items() if value is not None}


class CoreSchema(Schema):
    pass


T = TypeVar("T", bound="Object")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Object:
    schema: ClassVar[Type[Schema]] = Schema

    @classmethod
    def load(
        cls: Type[T],
        data: Dict[str, Any],
        only: Optional[Sequence[str]] = None,
        exclude: Sequence[str] = (),
        **kwargs: Any,
    ) -> T:
        schema = cls.schema(only=only, exclude=exclude)
        normalized_data = schema.load(data)
        normalized_data.update(kwargs)
        obj = converter.structure(normalized_data, cls)
        return obj

    def dump(
        self, only: Optional[Sequence[str]] = None, exclude: Sequence[str] = ()
    ) -> Dict[str, Any]:
        schema = self.schema(only=only, exclude=exclude)
        return schema.dump(self)

    def __repr__(self) -> str:
        if hasattr(self, "id") and hasattr(self, "name"):
            return f"{self.__class__.__qualname__}(name={self.name!r}, id={self.id!r})"
        elif hasattr(self, "id"):
            return f"{self.__class__.__qualname__}(id={self.id!r})"
        elif hasattr(self, "name"):
            return f"{self.__class__.__qualname__}(name={self.name!r})"
        else:
            return super().__repr__()

    def copy(self: T, deep: bool = True) -> T:
        if deep:
            return copy.deepcopy(self)
        else:
            return copy.copy(self)


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class CoreObject(Object):
    schema: ClassVar[Type[CoreSchema]] = CoreSchema
    api: Optional["Smartsheet"] = attr.ib(default=None, init=False)


TS = TypeVar("TS", bound=CoreObject)


class CRUD(Generic[TS]):
    base_url = ""
    _get_url: Optional[str] = None
    _list_url: Optional[str] = None
    _update_url: Optional[str] = None
    _create_url: Optional[str] = None
    _delete_url: Optional[str] = None

    get_include_fields: Optional[Sequence[str]] = None
    get_exclude_fields: Sequence[str] = ()
    list_include_fields: Optional[Sequence[str]] = None
    list_exclude_fields: Sequence[str] = ()
    create_include_fields: Optional[Sequence[str]] = None
    create_exclude_fields: Sequence[str] = ()
    update_include_fields: Optional[Sequence[str]] = None
    update_exclude_fields: Sequence[str] = ()

    factory: Type[TS] = cast(Type[TS], CoreObject)

    def __init__(self, smartsheet: Optional["Smartsheet"]) -> None:
        self.api = smartsheet

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

    @property
    def id_to_obj(self) -> Dict[str, TS]:
        return {obj.id: obj for obj in self.list()}

    @property
    def name_to_obj(self) -> Dict[str, TS]:
        return {obj.name: obj for obj in self.list()}

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
        if name is None and id is None:
            raise ValueError(f"To use get method, either name or id must be provided")
        elif id:
            endpoint = self.get_url.format(id=id)
            obj_data = self.api.get(endpoint, path=None)
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
            obj.api = self.api
            return obj
        else:
            id_ = self.name_to_obj[name].id
            return self.get(id=id_, **kwargs)

    def list(self) -> List[TS]:
        """Fetches a list of CoreObject objects.

        Note: API usually returns an incomplete view of objects.
        For example: /sheets will return a list of sheets without columns or rows

        Args:
            name: name of the object
            id: id of the object

        Returns:
            CoreObject
        """
        result = []
        for obj_data in self.api.get(self.list_url, params={"includeAll": "true"}):
            logger.debug(
                "Creating an object '%s' from data: %s",
                self.factory.__qualname__,
                str(obj_data),
            )
            obj = self.factory.load(
                obj_data, self.list_include_fields, self.list_exclude_fields
            )
            obj.api = self.api
            result.append(obj)
        return result

    def create(self, obj: TS) -> "Result":
        """Creates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        obj.api = self.api
        endpoint = self.create_url.format(obj=obj)
        return self.api.post(
            endpoint,
            obj.dump(
                only=self.create_include_fields, exclude=self.create_exclude_fields
            ),
        )

    def update(self, obj: TS) -> "Result":
        """Updates CoreObject

        Args:
            obj: CoreObject

        Returns:
            Result object
        """
        obj.api = self.api
        endpoint = self.update_url.format(id=obj.id)
        return self.api.put(
            endpoint,
            obj.dump(
                only=self.update_include_fields, exclude=self.update_exclude_fields
            ),
        )

    def delete(self, name: Optional[str] = None, id: Optional[int] = None) -> "Result":
        """Deletes CoreObject by name or id

        Args:
            name: CoreObject name attribute
            id: CoreObject id attribute

        Returns:
            Result object
        """
        if name is None and id is None:
            raise ValueError(
                f"To use delete method, either name or id must be provided"
            )
        elif id:
            endpoint = self.delete_url.format(id=id)
            return self.api.delete(endpoint)
        else:
            id_ = self.name_to_obj[name].id
            return self.delete(id=id_)

    def __iter__(self) -> Iterator[TS]:
        return iter(self.list())
