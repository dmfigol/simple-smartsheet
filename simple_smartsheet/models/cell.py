from datetime import datetime, date
from typing import Optional, Union, ClassVar, Type, Any, List

import attr
from marshmallow import fields
from marshmallow import utils

from simple_smartsheet.models.base import Schema, Object
from simple_smartsheet.models.extra import Hyperlink, HyperlinkSchema


class CellValueField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if isinstance(value, datetime):
            return utils.isoformat(value)
        elif isinstance(value, date):
            return utils.to_iso_date(value)
        else:
            return super()._serialize(value, attr, obj, **kwargs)


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

    schema: ClassVar[Type[CellSchema]] = CellSchema

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__qualname__}(column_id={self.column_id!r}, "
            f"value={self.value!r})"
        )
