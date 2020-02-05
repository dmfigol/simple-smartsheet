import logging
from datetime import datetime, date
from enum import Enum
from typing import Optional, Union, Any, List, ClassVar, Type

import attr
import marshmallow.utils
from marshmallow import fields, post_load, pre_load

from simple_smartsheet import utils
from simple_smartsheet.models.base import Schema, Object
from simple_smartsheet.models.extra import Hyperlink, HyperlinkSchema

logger = logging.getLogger(__name__)


# noinspection PyShadowingNames
class CellValueField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, datetime):
            return marshmallow.utils.isoformat(value)
        elif isinstance(value, date):
            return marshmallow.utils.to_iso_date(value)
        else:
            return super()._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        if not value:
            return value

        column_id_to_type = self.context["column_id_to_type"]
        if "virtualColumnId" in data:
            column_id = data["virtualColumnId"]
        else:
            column_id = data["columnId"]
        column_type = column_id_to_type[column_id]
        if column_type == "DATE":
            try:
                return marshmallow.utils.from_iso_date(value)  # type: ignore
            except ValueError:
                logger.warning("Cell value %r is not a valid date", value)
                return value
        elif column_type in ("DATETIME", "ABSTRACT_DATETIME"):
            try:
                return marshmallow.utils.from_iso_datetime(value)  # type: ignore
            except ValueError:
                logger.info("Cell value %r is not a valid datetime", value)
                return value
        elif column_type == "MULTI_PICKLIST":
            # TODO: implement once goes live
            pass
        return value


class ObjectType(Enum):
    ABSTRACT_DATETIME = "ABSTRACT_DATETIME"
    CONTACT = "CONTACT"
    DATE = "DATE"
    DATETIME = "DATETIME"
    DURATION = "DURATION"
    MULTI_CONTACT = "MULTI_CONTACT"
    MULTI_PICKLIST = "MULTI_PICKLIST"
    PREDECESSOR_LIST = "PREDECESSOR_LIST"


class LagSchema(Schema):
    object_type = fields.Str(data_key="objectType")
    days = fields.Int()
    elapsed = fields.Bool()
    hours = fields.Int()
    milliseconds = fields.Int()
    minutes = fields.Int()
    negative = fields.Bool()
    seconds = fields.Int()
    weeks = fields.Int()


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Lag(Object):
    object_type: ObjectType = ObjectType.DURATION
    days: Optional[int] = None
    elapsed: Optional[bool] = None
    hours: Optional[int] = None
    milliseconds: Optional[int] = None
    minutes: Optional[int] = None
    negative: Optional[bool] = None
    seconds: Optional[int] = None
    weeks: Optional[int] = None

    _schema = LagSchema


class PredecessorType(Enum):
    FF = "FF"
    FS = "FS"
    SF = "SF"
    SS = "SS"


class PredecessorSchema(Schema):
    row_id = fields.Int(data_key="rowId")
    type = fields.Str()
    in_critical_path = fields.Bool(data_key="inCriticalPath")
    invalid = fields.Bool()
    lag = fields.Nested(LagSchema)
    row_num = fields.Int()


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Predecessor(Object):
    row_id: int
    type: PredecessorType
    in_critical_path: Optional[bool] = None
    invalid: Optional[bool] = None
    lag: Lag
    row_num: int

    _schema = PredecessorSchema


class ObjectValueSchema(Schema):
    object_type = fields.Str(data_key="objectType")
    predecessors = fields.List(fields.Nested(PredecessorSchema))
    values = fields.Field()
    value = fields.Field()


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class ObjectValue(Object):
    object_type: ObjectType
    predecessors: Optional[List[Predecessor]] = None
    values: Any = None
    value: Any = None

    _schema: ClassVar[Type[Schema]] = ObjectValueSchema

    def __repr__(self) -> str:
        return utils.create_repr(self, ("object_type", "values"))


class CellSchema(Schema):
    column_id = fields.Int(data_key="columnId")
    column_type = fields.Str(data_key="columnType")
    conditional_format = fields.Str(data_key="conditionalFormat")
    display_value = fields.Str(data_key="displayValue")
    format = fields.Str()
    formula = fields.Str()
    hyperlink = fields.Nested(HyperlinkSchema)
    image = fields.Field()  # TODO: Image object
    link_in_from_cell = fields.Field(data_key="linkInFromCell")  # TODO: CellLink object
    link_out_to_cells = fields.List(
        fields.Field(), data_key="linksOutToCells"
    )  # TODO: CellLink object
    object_value = fields.Nested(
        ObjectValueSchema, data_key="objectValue", allow_none=True
    )
    override_validation = fields.Bool(data_key="overrideValidation")
    strict = fields.Bool()
    value = CellValueField()

    @post_load
    def fix_checkbox_value(self, data, many: bool, **kwargs):
        column_id_to_type = self.context["column_id_to_type"]
        if "virtual_column_id" in data:
            column_id = data["virtual_column_id"]
        else:
            column_id = data["column_id"]
        column_type = column_id_to_type[column_id]
        if column_type == "CHECKBOX" and "value" not in data:
            data["value"] = False
        return data

    @pre_load
    def fix_object_value(self, data, **kwargs):
        if "value" in data and "objectValue" in data:
            data["objectValue"] = None
        return data


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Cell(Object):
    column_id: Optional[int] = None
    column_type: Optional[str] = None
    conditional_format: Optional[str] = None
    display_value: Optional[str] = None
    format: Optional[str] = None
    formula: Optional[str] = None
    hyperlink: Optional[Hyperlink] = None
    image: Optional[Any] = None  # TODO: Image object
    link_in_from_cell: Optional[Any] = None  # TODO: CellLink object
    link_out_to_cells: Optional[List[Any]] = None  # TODO: CellLink object
    object_value: Optional[ObjectValue] = None
    override_validation: Optional[bool] = None
    strict: bool = True
    value: Union[float, str, datetime, None] = None

    _schema = CellSchema

    def __repr__(self) -> str:
        return utils.create_repr(self, ["column_id", "value"])

    @property
    def _column_id(self) -> Optional[int]:
        return self.column_id

    @classmethod
    def create_multi_picklist(cls, column_id: int, values: List[str]) -> "Cell":
        cell = cls(
            column_id=column_id,
            object_value=ObjectValue(
                object_type=ObjectType.MULTI_PICKLIST, values=values,
            ),
        )
        return cell

    def get_value(self) -> Any:
        if self.object_value and self.object_value.values:
            return self.object_value.values
        if self.display_value and self.display_value.isdigit():
            return int(self.display_value)
        else:
            return self.value
