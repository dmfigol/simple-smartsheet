import logging
from typing import Optional, List

import attr
from marshmallow import fields

from simple_smartsheet.crud import CRUDRead
from simple_smartsheet.models.cell import Cell, CellSchema
from simple_smartsheet.models.column import Column, ColumnSchema
from simple_smartsheet.models.row import _RowBase, RowSchema
from simple_smartsheet.models.sheet import Sheet, _SheetBase, SheetSchema

logger = logging.getLogger(__name__)


class ReportCellSchema(CellSchema):
    virtual_column_id = fields.Int(data_key="virtualColumnId")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class ReportCell(Cell):
    virtual_column_id: Optional[int] = None

    _schema = ReportCellSchema

    @property
    def _column_id(self) -> Optional[int]:
        return self.virtual_column_id


class ReportRowSchema(RowSchema):
    cells = fields.Nested(ReportCellSchema, many=True)
    sheet_id = fields.Int(data_key="sheetId")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class ReportRow(_RowBase[ReportCell]):
    sheet_id: Optional[int] = None
    cells: List[ReportCell] = attr.Factory(list)

    _schema = ReportRowSchema


class ReportColumnSchema(ColumnSchema):
    virtual_id = fields.Int(data_key="virtualId")
    sheet_name_column = fields.Bool(data_key="sheetNameColumn")

    @property
    def _id_attr(self):
        return "virtual_id"


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class ReportColumn(Column):
    virtual_id: Optional[int] = None
    sheet_name_column: Optional[bool] = None

    _schema = ReportColumnSchema

    @property
    def _id(self) -> Optional[int]:
        return self.virtual_id


class ReportSchema(SheetSchema):
    """Marshmallow Schema for Smartsheet Report object

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#reports
    """

    columns = fields.Nested(ReportColumnSchema, many=True)
    rows = fields.Nested(ReportRowSchema, many=True)
    source_sheets = fields.Nested(SheetSchema, many=True, data_key="sourceSheets")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Report(_SheetBase[ReportRow, ReportColumn]):
    """Represents Smartsheet Report object

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#reports
    """

    columns: List[ReportColumn] = attr.Factory(list)
    rows: List[ReportRow] = attr.Factory(list)

    source_sheets: List[Sheet] = attr.Factory(list)
    _schema = ReportSchema


class ReportCRUD(CRUDRead[Report]):
    base_url = "/reports"
    factory = Report
