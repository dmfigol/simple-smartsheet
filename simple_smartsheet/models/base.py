import logging
import copy as cp
from datetime import datetime
from typing import (
    TypeVar,
    Dict,
    Any,
    Optional,
    Type,
    Union,
    ClassVar,
    Sequence,
)


import attr
import marshmallow
from marshmallow import fields
from cattr.converters import Converter

from simple_smartsheet import config
from simple_smartsheet import utils
from simple_smartsheet.types import IndexesType


logger = logging.getLogger(__name__)

converter = Converter()  # type: ignore
converter.register_structure_hook(datetime, lambda ts, _: ts)
converter.register_structure_hook(IndexesType, lambda x, _: x)
converter.register_structure_hook(Union[float, str, datetime, None], lambda ts, _: ts)


class Schema(marshmallow.Schema):
    class Meta:
        unknown = utils.get_unknown_field_handling(config.STRICT_VALIDATION)

    @marshmallow.post_dump
    def remove_none(self, data, many: bool, **kwargs):
        return {key: value for key, value in data.items() if value is not None}


class CoreSchema(Schema):
    id = fields.Int()
    name = fields.Str()


T = TypeVar("T", bound="Object")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Object:
    _schema: ClassVar[Type[Schema]] = Schema

    @classmethod
    def load(
        cls: Type[T],
        data: Dict[str, Any],
        only: Optional[Sequence[str]] = None,
        exclude: Sequence[str] = (),
        **kwargs: Any,
    ) -> T:
        schema = cls._schema(only=only, exclude=exclude)
        normalized_data = schema.load(data)
        normalized_data.update(kwargs)
        obj = converter.structure(normalized_data, cls)
        return obj

    def dump(
        self, only: Optional[Sequence[str]] = None, exclude: Sequence[str] = ()
    ) -> Dict[str, Any]:
        schema = self._schema(only=only, exclude=exclude)
        result = schema.dump(self.unstructured)
        return result

    @property
    def unstructured(self) -> Dict[str, Any]:
        return converter.unstructure(self)

    def __repr__(self) -> str:
        if hasattr(self, "id") and hasattr(self, "name"):
            attrs = ["name", "id"]
        elif hasattr(self, "id"):
            attrs = ["id"]
        elif hasattr(self, "name"):
            attrs = ["name"]
        else:
            return super().__repr__()
        return utils.create_repr(self, attrs)

    def copy(self: T, deep: bool = True) -> T:
        if deep:
            return cp.deepcopy(self)
        else:
            return cp.copy(self)


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class CoreObject(Object):
    name: str
    id: Optional[int] = None

    _schema: ClassVar[Type[CoreSchema]] = CoreSchema

    @property
    def _id(self) -> Optional[int]:
        return getattr(self, "id")

    @property
    def _name(self) -> str:
        return getattr(self, "name")
