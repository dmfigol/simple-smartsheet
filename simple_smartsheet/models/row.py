import logging
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING, Dict, Tuple, Any, ClassVar, Type, cast

import attr
from marshmallow import fields

from simple_smartsheet import utils
from simple_smartsheet.models.base import Schema, Object
from simple_smartsheet.models.cell import Cell, CellSchema
from simple_smartsheet.models.column import Column, ColumnSchema

if TYPE_CHECKING:
    from simple_smartsheet.models.sheet import Sheet

logger = logging.getLogger(__name__)


class RowSchema(Schema):
    id = fields.Int()
    sheet_id = fields.Int(data_key="sheetId")
    access_level = fields.Str(data_key="accessLevel")
    attachments = fields.List(fields.Field())  # TODO: Attachment object
    cells = fields.Nested(CellSchema, many=True)
    columns = fields.Nested(ColumnSchema, many=True)
    conditional_format = fields.Str(data_key="conditionalFormat")
    created_at = fields.DateTime(data_key="createdAt")
    created_by = fields.Field(data_key="createdBy")  # TODO: User object
    discussions = fields.List(fields.Field())  # TODO: Discussion object
    expanded = fields.Bool()
    filtered_out = fields.Bool(data_key="filteredOut")
    format = fields.Str()
    in_critical_path = fields.Bool(data_key="inCriticalPath")
    locked = fields.Bool()
    locked_for_user = fields.Bool(data_key="lockedForUser")
    modified_at = fields.DateTime(data_key="modifiedAt")
    modified_by = fields.Field(data_key="modifiedBy")  # TODO: User object
    num = fields.Int(data_key="rowNumber")
    permalink = fields.Str()
    version = fields.Int()

    # location-specifier attributes
    parent_id = fields.Int(data_key="parentId")
    sibling_id = fields.Int(data_key="siblingId")
    above = fields.Bool()
    indent = fields.Int()
    outdent = fields.Int()
    to_bottom = fields.Bool(data_key="toBottom")
    to_top = fields.Bool(data_key="toTop")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Row(Object):
    id: Optional[int] = None
    sheet_id: Optional[int] = None
    access_level: Optional[str] = None
    attachments: List[Any] = attr.Factory(list)
    cells: List[Cell] = attr.Factory(list)
    columns: List[Column] = attr.Factory(list)
    conditional_format: Optional[str] = None
    created_at: Optional[datetime] = None
    created_by: Optional[Any] = None
    discussions: List[Any] = attr.Factory(list)
    expanded: Optional[bool] = None
    filtered_out: Optional[bool] = None
    format: Optional[str] = None
    in_critical_path: Optional[bool] = None
    locked: Optional[bool] = None
    locked_for_user: Optional[bool] = None
    modified_at: Optional[datetime] = None
    modified_by: Optional[Any] = None
    num: Optional[int] = None
    permalink: Optional[str] = None
    version: Optional[int] = None

    # location-specified attributes
    parent_id: Optional[int] = None
    sibling_id: Optional[int] = None
    above: Optional[bool] = None
    indent: Optional[int] = None
    outdent: Optional[int] = None
    to_bottom: Optional[bool] = None
    to_top: Optional[bool] = None

    # index
    column_title_to_cell: Dict[str, Cell] = attr.Factory(dict)
    column_id_to_cell: Dict[int, Cell] = attr.Factory(dict)

    schema: ClassVar[Type[RowSchema]] = RowSchema

    def __repr__(self) -> str:
        return utils.create_repr(self, ["id", "num"])

    def update_index(
        self,
        sheet: "Sheet",
        index_key_to_unique: Dict[Tuple[str, ...], bool],
        deserealize_cell_values: bool = False,
    ) -> None:
        self.column_title_to_cell.clear()
        self.column_id_to_cell.clear()

        for cell in self.cells:
            column_id = cell.column_id
            if column_id is None:
                continue
            column = sheet.get_column(column_id=column_id)
            column_title = column.title

            self.column_id_to_cell[column_id] = cell
            if column_title is not None:
                self.column_title_to_cell[column_title] = cell

            if deserealize_cell_values:
                cell.deserealize_value(self, column)

        for index_key, unique in index_key_to_unique.items():
            index = sheet.indexes[index_key]
            key = tuple(self.get_cell(column_title).value for column_title in index_key)
            if unique:
                index[key] = self
            else:
                container = cast(List["Row"], index.setdefault(key, []))
                container.append(self)

    def get_cell(
        self, column_title: Optional[str] = None, column_id: Optional[int] = None
    ) -> Cell:
        if column_title is not None:
            return self.column_title_to_cell[column_title]
        elif column_id is not None:
            return self.column_id_to_cell[column_id]
        else:
            raise ValueError(
                "Either column_title or column_id argument should be provided"
            )

    def as_dict(self) -> Dict[str, Any]:
        """Returns a dictionary of column title to cell value"""
        return {
            column_title: cell.value
            for column_title, cell in self.column_title_to_cell.items()
        }
