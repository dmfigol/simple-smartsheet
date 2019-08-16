import logging
from typing import Optional, List, Dict, Any, cast

import attr
from marshmallow import fields

from simple_smartsheet.crud import CRUDRead, AsyncCRUDRead, CRUDAttrs
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
    cells = fields.List(fields.Nested(ReportCellSchema))
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

    columns = fields.List(fields.Nested(ReportColumnSchema))
    rows = fields.List(fields.Nested(ReportRowSchema))
    source_sheets = fields.List(fields.Nested(SheetSchema, data_key="sourceSheets"))
    is_summary = fields.Bool(data_key="isSummaryReport")
    read_only = fields.Bool(data_key="readOnly")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Report(_SheetBase[ReportRow, ReportColumn]):
    """Represents Smartsheet Report object

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#reports
    """

    columns: List[ReportColumn] = attr.Factory(list)
    rows: List[ReportRow] = attr.Factory(list)

    source_sheets: List[Sheet] = attr.Factory(list)
    is_summary: bool = False
    read_only: Optional[bool] = None

    _schema = ReportSchema


class ReportCRUDMixin(CRUDAttrs):
    base_url = "/reports"
    get_params = {"pageSize": "10000"}


class ReportCRUD(ReportCRUDMixin, CRUDRead[Report]):
    factory = Report

    def _get_by_id(self, id: int) -> Report:
        endpoint = self.get_url.format(id=id)
        page = 1
        data = cast(
            Dict[str, Any],
            self.smartsheet._get(endpoint, path=None, params=self.get_params),
        )
        full_data = data
        while data["totalRowCount"] != len(full_data["rows"]):
            page += 1
            params = {"page": str(page)}
            if self.get_params:
                params.update(self.get_params)
            data = cast(
                Dict[str, Any], self.smartsheet._get(endpoint, path=None, params=params)
            )
            full_data["rows"].extend(data["rows"])
        return self._create_obj_from_data(full_data)


class ReportAsyncCRUD(ReportCRUDMixin, AsyncCRUDRead[Report]):
    factory = Report

    async def _get_by_id(self, id: int) -> Report:
        endpoint = self.get_url.format(id=id)
        page = 1
        data = cast(
            Dict[str, Any],
            await self.smartsheet._get(endpoint, path=None, params=self.get_params),
        )
        full_data = data
        while data["totalRowCount"] != len(full_data["rows"]):
            page += 1
            params = {"page": str(page)}
            if self.get_params:
                params.update(self.get_params)
            data = cast(
                Dict[str, Any],
                await self.smartsheet._get(endpoint, path=None, params=params),
            )
            full_data["rows"].extend(data["rows"])
        return self._create_obj_from_data(full_data)
