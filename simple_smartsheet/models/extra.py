from typing import Optional, ClassVar, Type, List, Any

import attr
from marshmallow import fields

from simple_smartsheet.models.base import Schema, Object


class AutoNumberFormatSchema(Schema):
    fill = fields.Str()
    prefix = fields.Str()
    starting_num = fields.Str(data_key="startingNumber")
    suffix = fields.Str()


@attr.s(auto_attribs=True, kw_only=True)
class AutoNumberFormat(Object):
    fill: str
    prefix: str
    starting_num: int
    suffix: str


class ErrorSchema(Schema):
    error_code = fields.Int(data_key="errorCode")
    message = fields.Str()
    ref_id = fields.Str(data_key="refId")
    detail = fields.Field()


@attr.s(auto_attribs=True, kw_only=True)
class Error(Object):
    error_code: int
    message: str
    ref_id: str
    detail: Optional[Any] = None

    schema: ClassVar[Type[ErrorSchema]] = ErrorSchema


class ResultSchema(Schema):
    failed_items = fields.List(fields.Field(), data_key="failedItems")
    message = fields.Str()
    result = fields.Field()
    result_code = fields.Int(data_key="resultCode")
    version = fields.Int()


@attr.s(auto_attribs=True, kw_only=True)
class Result(Object):
    failed_items: List[Any] = attr.Factory(list)
    message: Optional[str] = None
    result: Optional[Any] = None
    result_code: Optional[int] = None
    version: Optional[int] = None

    schema: ClassVar[Type[ResultSchema]] = ResultSchema


class HyperlinkSchema(Schema):
    report_id = fields.Int(data_key="reportId")
    sheet_id = fields.Int(data_key="sheetId")
    sight_id = fields.Int(data_key="sightId")
    url = fields.Str()


@attr.s(auto_attribs=True, kw_only=True)
class Hyperlink(Object):
    url: str
    report_id: Optional[int] = None
    sheet_id: Optional[int] = None
    sight_id: Optional[int] = None

    schema: ClassVar[Type[HyperlinkSchema]] = HyperlinkSchema
