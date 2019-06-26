import logging
from datetime import datetime, date
from typing import Optional, Union, ClassVar, Type, Any, List

import attr
import marshmallow.utils
from marshmallow import fields, post_load

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
        column_id_to_type = self.context["column_id_to_type"]
        if "virtualColumnId" in data:
            column_id = data["virtualColumnId"]
        else:
            column_id = data["columnId"]
        column_type = column_id_to_type[column_id]
        if not value:
            return value
        if column_type == "DATE":
            try:
                return marshmallow.utils.from_iso_date(value)
            except ValueError:
                logger.warning("Cell value %r is not a valid date", value)
                return value
        elif column_type in ("DATETIME", "ABSTRACT_DATETIME"):
            try:
                return marshmallow.utils.from_iso_datetime(value)
            except ValueError:
                logger.info("Cell value %r is not a valid datetime ", value)
                return value
        return value


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
    object_value = fields.Field(data_key="objectValue")  # TODO: ObjectValue object
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
    object_value: Optional[Any] = None  # TODO: ObjectValue object
    override_validation: Optional[bool] = None
    strict: bool = True
    value: Union[float, str, datetime, None] = None

    _schema: ClassVar[Type[CellSchema]] = CellSchema

    def __repr__(self) -> str:
        return utils.create_repr(self, ["column_id", "value"])

    @property
    def _column_id(self) -> Optional[int]:
        return self.column_id
