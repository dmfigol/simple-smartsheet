from enum import Enum
from typing import Optional, List

import attr
from marshmallow import fields, post_load

from simple_smartsheet import utils
from simple_smartsheet.models.base import Schema, Object
from simple_smartsheet.models.extra import AutoNumberFormatSchema, AutoNumberFormat


class ContactOptionSchema(Schema):
    email = fields.Str()
    name = fields.Str()


@attr.s(auto_attribs=True, kw_only=True)
class ContactOption(Object):
    email: str
    name: Optional[str] = None


class ColumnType(Enum):
    TEXT_NUMBER = "TEXT_NUMBER"
    PICKLIST = "PICKLIST"
    CHECKBOX = "CHECKBOX"
    DATE = "DATE"
    DATETIME = "DATETIME"
    ABSTRACT_DATETIME = "ABSTRACT_DATETIME"
    CONTACT_LIST = "CONTACT_LIST"
    MULTI_CONTACT_LIST = "MULTI_CONTACT_LIST"
    DURATION = "DURATION"
    PREDECESSOR = "PREDECESSOR"


class ColumnSchema(Schema):
    id = fields.Int()
    system_column_type = fields.Str(data_key="systemColumnType")
    type = fields.Str()
    auto_number_format = fields.Nested(
        AutoNumberFormatSchema, data_key="autoNumberFormat"
    )
    contact_options = fields.List(
        fields.Nested(ContactOptionSchema, data_key="contactOptions")
    )
    format = fields.Str()
    hidden = fields.Bool()
    index = fields.Int()
    locked = fields.Bool()
    locked_for_user = fields.Bool(data_key="lockedForUser")
    options = fields.List(fields.Str())
    primary = fields.Bool()
    symbol = fields.Str()
    tags = fields.List(fields.Str())
    title = fields.Str()
    validation = fields.Bool()
    version = fields.Int()
    width = fields.Int()

    @property
    def _id_attr(self):
        return "id"

    @post_load
    def post_load_update_parent_context(self, data, many: bool, **kwargs):
        column_id_to_type = self.context["column_id_to_type"]
        id_ = data[self._id_attr]
        type_ = data["type"]
        column_id_to_type[id_] = type_
        return data


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Column(Object):
    id: Optional[int] = None
    system_column_type: Optional[str] = None
    type: Optional[ColumnType] = None
    auto_number_format: Optional[AutoNumberFormat] = None
    contact_options: Optional[List[ContactOption]] = None
    format: Optional[str] = None
    hidden: Optional[bool] = None
    index: Optional[int] = None
    locked: Optional[bool] = None
    locked_for_user: Optional[bool] = None
    options: Optional[List[str]] = None
    primary: Optional[bool] = None
    symbol: Optional[str] = None
    tags: Optional[List[str]] = None
    title: Optional[str] = None
    validation: Optional[bool] = None
    version: Optional[int] = None
    width: Optional[int] = None

    @property
    def _id(self) -> Optional[int]:
        return self.id

    def __repr__(self) -> str:
        return utils.create_repr(self, ["id", "title"])
