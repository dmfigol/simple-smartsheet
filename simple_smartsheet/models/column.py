from typing import Optional, List

import attr
from marshmallow import fields

from simple_smartsheet.models.base import Schema, Object
from simple_smartsheet.models.extra import AutoNumberFormatSchema, AutoNumberFormat


class ContactOptionSchema(Schema):
    email = fields.Str()
    name = fields.Str()


@attr.s(auto_attribs=True, kw_only=True)
class ContactOption(Object):
    email: str
    name: str


class ColumnSchema(Schema):
    id = fields.Int()
    system_column_type = fields.Str(data_key="systemColumnType")
    type = fields.Str()  # TODO: should be enum
    auto_number_format = fields.Nested(
        AutoNumberFormatSchema, data_key="autoNumberFormat"
    )
    contact_options = fields.Nested(ContactOptionSchema, data_key="contactOptions")
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


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Column(Object):
    id: Optional[int] = None
    system_column_type: Optional[str] = None
    type: Optional[str] = None
    auto_number_format: Optional[AutoNumberFormat] = None
    contact_options: Optional[ContactOption] = None
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

    def __repr__(self) -> str:
        return f"{self.__class__.__qualname__}(id={self.id!r}, title={self.title!r})"
