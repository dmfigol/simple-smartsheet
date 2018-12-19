import logging
from collections import defaultdict
from datetime import datetime
from typing import (
    Optional,
    Dict,
    List,
    ClassVar,
    Type,
    Sequence,
    Tuple,
    Any,
    Union,
    cast,
)

import attr
from marshmallow import fields


from simple_smartsheet.models.base import Schema, CoreSchema, Object, CoreObject, CRUD
from simple_smartsheet.models.column import Column, ColumnSchema
from simple_smartsheet.models.row import Row, RowSchema
from simple_smartsheet.models.cell import Cell
from simple_smartsheet.models.extra import Result
from simple_smartsheet.types import IndexesKeysType, IndexesType


logger = logging.getLogger(__name__)


class UserSettingsSchema(Schema):
    critical_path_enabled = fields.Bool(data_key="criticalPathEnabled")
    display_summary_tasks = fields.Bool(data_key="displaySummaryTasks")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class UserSettings(Object):
    critical_path_enabled: bool
    display_summary_tasks: bool


class WorkspaceSchema(Schema):
    id = fields.Int()
    name = fields.Str()


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Workspace(Object):
    id: int
    name: str


class SheetSchema(CoreSchema):
    """Marshmallow Schema for Smartsheet Sheet object

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#sheets

    """

    id = fields.Int()
    name = fields.Str()
    access_level = fields.Str(data_key="accessLevel")
    permalink = fields.Str()
    favorite = fields.Bool()
    created_at = fields.DateTime(data_key="createdAt")
    modified_at = fields.DateTime(data_key="modifiedAt")

    version = fields.Int()
    total_row_count = fields.Int(data_key="totalRowCount")
    effective_attachment_options = fields.List(
        fields.Str(), data_key="effectiveAttachmentOptions"
    )
    gantt_enabled = fields.Bool(data_key="ganttEnabled")
    dependencies_enabled = fields.Bool(data_key="dependenciesEnabled")
    resource_management_enabled = fields.Bool(data_key="resourceManagementEnabled")
    cell_image_upload_enabled = fields.Bool(data_key="cellImageUploadEnabled")
    user_settings = fields.Nested(UserSettingsSchema, data_key="userSettings")

    columns = fields.Nested(ColumnSchema, many=True)
    rows = fields.Nested(RowSchema, many=True)
    workspace = fields.Nested(WorkspaceSchema)


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class Sheet(CoreObject):
    """Represent Smartsheet Sheet object

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#sheets

    Extra attributes:
        row_rum_to_row: mapping of row number to Row object
        row_id_to_row: mapping of row id to Row object
        column_title_to_column: mapping of column title to Column object
        column_id_to_column: mapping of column id to Column object
        schema: reference to SheetSchema
    """

    name: str
    id: Optional[int] = None
    access_level: Optional[str] = None
    permalink: Optional[str] = None
    favorite: Optional[bool] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None

    version: Optional[int] = None
    total_row_count: Optional[int] = None
    effective_attachment_options: List[str] = attr.Factory(list)
    gantt_enabled: Optional[bool] = None
    dependencies_enabled: Optional[bool] = None
    resource_management_enabled: Optional[bool] = None
    cell_image_upload_enabled: Optional[bool] = None
    user_settings: Optional[UserSettings] = None

    columns: List[Column] = attr.Factory(list)
    rows: List[Row] = attr.Factory(list)
    workspace: Optional[Workspace] = None

    row_num_to_row: Dict[int, Row] = attr.Factory(dict)
    row_id_to_row: Dict[int, Row] = attr.Factory(dict)
    column_title_to_column: Dict[str, Column] = attr.Factory(dict)
    column_id_to_column: Dict[int, Column] = attr.Factory(dict)

    index_keys: IndexesKeysType = attr.Factory(list)
    index_key_to_unique: Dict[Tuple[str, ...], bool] = attr.Factory(dict)
    indexes: IndexesType = attr.Factory(lambda: defaultdict(dict))

    schema: ClassVar[Type[SheetSchema]] = SheetSchema

    def __attrs_post_init__(self) -> None:
        self.update_index()

    def update_index(self) -> None:
        """Updates columns and row indices for quick lookup"""
        for index_key_dict in self.index_keys:
            columns = index_key_dict["columns"]
            unique = index_key_dict["unique"]
            self.index_key_to_unique[tuple(sorted(columns))] = unique

        self.update_column_index()
        self.update_row_index(self.index_key_to_unique)

    def update_column_index(self) -> None:
        """Updates columns index for quick lookup by title and ID"""
        self.column_title_to_column.clear()
        self.column_id_to_column.clear()

        for column in self.columns:
            if column.id is None:
                continue
            self.column_id_to_column[column.id] = column

            column_title = column.title
            if column_title is None:
                continue
            if column_title in self.column_title_to_column:
                logger.info(
                    "Column with the title %s is already present in the index"
                    % column_title
                )
            self.column_title_to_column[column_title] = column

    def update_row_index(self, index_keys: IndexesKeysType) -> None:
        """Updates row index for quick lookup by row number and ID"""
        self.row_num_to_row.clear()
        self.row_id_to_row.clear()

        for row in self.rows:
            self.row_num_to_row[row.num] = row
            self.row_id_to_row[row.id] = row
            row.update_index(self, index_keys)

    def get_row(
        self,
        row_num: Optional[int] = None,
        row_id: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> Optional[Row]:
        """Returns Row object by row number or ID

        Either row_num or row_id must be provided

        Args:
            row_num: row number
            row_id: row id
            filter: a dictionary or ordered dictionary with column title to value
        mappings in the same order as index was built. Index must be unique.

        Returns:
            Row object
        """
        if row_num is not None:
            return self.row_num_to_row.get(row_num)
        elif row_id is not None:
            return self.row_id_to_row.get(row_id)
        elif filter is not None:
            index_key, query = zip(*sorted(filter.items()))
            unique = self.index_key_to_unique.get(index_key)
            if unique is None:
                raise ValueError("Index %s was not built", index_key)
            elif not unique:
                raise ValueError(
                    "Index %s is non-unique and lookup will potentially "
                    "return multiple rows, use get_rows method instead",
                    index_key,
                )
            index = cast(Dict[Tuple, Row], self.indexes[index_key])
            return index[query]
        else:
            raise ValueError("Either row_num or row_id argument should be provided")

    def get_rows(self, filter: Dict[str, Any]) -> [List[Row]]:
        """Returns Row objects by index query

        Args:
            filter: a dictionary or ordered dictionary with column title to value
        mappings in the same order as index was built. Index must be non-unique.

        Returns:
            Row object
        """
        index_key, query = zip(*sorted(filter.items()))
        unique = self.index_key_to_unique.get(index_key)
        if unique is None:
            raise ValueError("Index %s was not built", index_key)
        elif unique:
            index = cast(Dict[Tuple, Row], self.indexes[index_key])
            result = index.get(query)
            if result is not None:
                return [result]
            else:
                return []
        else:
            index = cast(Dict[Tuple, List[Row]], self.indexes[index_key])
            return index.get(query, [])

    def get_column(
        self, column_title: Optional[str] = None, column_id: Optional[int] = None
    ) -> Optional[Column]:
        """Returns Column object by column title or ID

        Either column_title or column_id must be provided

        Args:
            column_title: column title (case-sensitive)
            column_id: column id

        Returns:
            Column object
        """
        if column_title is not None:
            return self.column_title_to_column.get(column_title)
        elif column_id is not None:
            return self.column_id_to_column.get(column_id)
        else:
            raise ValueError(
                "Either column_title or column_id argument should be provided"
            )

    def add_rows(self, rows: Sequence[Row]) -> Result:
        """Adds several rows to the smartsheet.

        Sheet must have api attribute set. It is automatically set when method
            Smartsheet.sheets.get() is used
        Every row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            rows: sequence of Row objects

        Returns:
            Result object
        """
        if self.api is None:
            raise ValueError("To use this method, api attribute must be set")
        include_fields = (
            "parent_id",
            "sibling_id",
            "above",
            "indent",
            "outdent",
            "to_bottom",
            "to_top",
            "expanded",
            "format",
            "cells.column_id",
            "cells.formula",
            "cells.value",
            "cells.hyperlink",
            "cells.link_in_from_cell",
            "cells.strict",
            "cells.format",
            "cells.image",
            "cells.override_validation",
            "locked",
        )
        data = []
        schema = RowSchema(only=include_fields)
        for row in rows:
            new_row = row.copy(deep=False)
            new_row.cells = [
                cell
                for cell in row.cells
                if cell.value is not None or cell.formula is not None
            ]
            data.append(schema.dump(new_row))
        return self.api.post(f"/sheets/{self.id}/rows", data=data)

    def add_row(self, row: Row) -> Result:
        """Adds a single row to the smartsheet.

        Sheet must have api attribute set. It is automatically set when method
            Smartsheet.sheets.get() is used
        A row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            row: Row object

        Returns:
            Result object
        """
        return self.add_rows([row])

    def update_rows(self, rows: Sequence[Row]) -> Result:
        """Updates several rows in the Sheet.

        Sheet must have api attribute set. It is automatically set when method
            Smartsheet.sheets.get() is used
        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            rows: sequence of Row objects

        Returns:
            Result object
        """
        if self.api is None:
            raise ValueError("To use this method, api attribute must be set")
        include_fields = (
            "id",
            "parent_id",
            "above",
            "indent",
            "outdent",
            "to_bottom",
            "to_top",
            "expanded",
            "format",
            "cells.column_id",
            "cells.formula",
            "cells.value",
            "cells.hyperlink",
            "cells.link_in_from_cell",
            "cells.strict",
            "cells.format",
            "cells.image",
            "cells.override_validation",
            "locked",
        )
        data = []
        schema = RowSchema(only=include_fields)
        for row in rows:
            new_row = row.copy(deep=False)
            new_row.cells = [
                cell
                for cell in row.cells
                if cell.value is not None or cell.formula is not None
            ]
            data.append(schema.dump(new_row))
        return self.api.put(f"/sheets/{self.id}/rows", data=data)

    def update_row(self, row: Row) -> Result:
        """Updates a single row in the Sheet.

        Sheet must have api attribute set. It is automatically set when method
            Smartsheet.sheets.get() is used
        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            row: Row object

        Returns:
            Result object
        """
        return self.update_rows([row])

    def delete_rows(self, row_ids: Sequence[int]) -> Result:
        """Deletes several rows in the Sheet.

        Rows are identified by ids.

        Args:
            row_ids: sequence of row ids

        Returns:
            Result object
        """
        if self.api is None:
            raise ValueError("To use this method, api attribute must be set")
        endpoint = f"/sheets/{self.id}/rows"
        params = {"ids": ",".join(str(row_id) for row_id in row_ids)}
        return self.api.delete(endpoint, params=params)

    def delete_row(self, row_id: int) -> Result:
        """Deletes a single row in the Sheet specified by ID.

        Args:
            row_id: Row id

        Returns:
            Result object
        """
        return self.delete_rows([row_id])

    def sort_rows(self, order: List[Dict[str, Any]]) -> "Sheet":
        """Sorts rows in the sheet with the specified order


        Args:
            order: List of dictionaries containing column_title or column_id and
                (optional) descending bool (default is ascending). Example:
                [
                    {"column_title": "Birth date", "descending": True},
                    {"column_title": "Full Name"}
                ]

        Returns:
            Sheet object
        """
        # TODO: add validation schema for sorting order
        normalized_order = []
        for item in order:
            normalized_item = {}
            if "column_id" in item:
                normalized_item["columnId"] = item["column_id"]
            elif "column_title" in item:
                column_title = item["column_title"]
                column = self.get_column(column_title)
                normalized_item["columnId"] = column.id
            else:
                raise ValueError(
                    "Sorting key must have either column_id or column_title"
                )

            descending = item.get("descending", False)
            if descending:
                normalized_item["direction"] = "DESCENDING"
            else:
                normalized_item["direction"] = "ASCENDING"
            normalized_order.append(normalized_item)

        data = {"sortCriteria": normalized_order}
        endpoint = f"/sheets/{self.id}/sort"
        response = self.api.post(endpoint, data, result_obj=False)
        sheet = self.load(response)
        sheet.api = self.api
        return sheet

    def make_cell(
        self, column_title: str, field_value: Union[float, str, datetime, None]
    ) -> Cell:
        """Creates a Cell object for an existing column

        Args:
            column_title: title of an existing column
            field_value: value of the cell

        Returns:
            Cell object
        """
        column = self.get_column(column_title)
        if column is None:
            raise ValueError(
                "A column with the title %s does not exist in this sheet", column_title
            )
        cell = Cell(column_id=column.id, value=field_value)
        return cell

    def make_cells(
        self, fields: Dict[str, Union[float, str, datetime, None]]
    ) -> List[Cell]:
        """Create a list of Cell objects from dictionary

        Args:
            fields: dictionary where key is a column title and value is a cell value

        Returns:
            list of Cell objects
        """
        result: List[Cell] = []
        for column_title, field_value in fields.items():
            result.append(self.make_cell(column_title, field_value))
        return result

    def as_list(self) -> List[Dict[str, Union[float, str, datetime, None]]]:
        """Returns a list of dictionaries with column titles and cell values"""
        return [row.as_dict() for row in self.rows]


class SheetsCRUD(CRUD[Sheet]):
    base_url = "/sheets"
    factory = Sheet
    default_path = "sheets"

    create_include_fields = (
        "name",
        "columns.primary",
        "columns.title",
        "columns.type",
        "columns.auto_number_format",
        "columns.options",
        "columns.symbol",
        "columns.system_column_type",
        "columns.width",
    )
