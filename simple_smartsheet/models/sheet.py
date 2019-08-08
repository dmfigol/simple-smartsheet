import logging
import warnings
from datetime import datetime
from typing import (
    Optional,
    Dict,
    List,
    ClassVar,
    Generic,
    Type,
    TypeVar,
    Sequence,
    Tuple,
    Any,
    Union,
    cast,
)

import attr
from marshmallow import fields, pre_load

from simple_smartsheet import config
from simple_smartsheet import exceptions
from simple_smartsheet import smartsheet
from simple_smartsheet import utils
from simple_smartsheet.crud import CRUD, AsyncCRUD, CRUDAttrs
from simple_smartsheet.types import IndexKeysDict, IndexesType
from simple_smartsheet.models.base import Schema, CoreSchema, Object, CoreObject
from simple_smartsheet.models.cell import Cell
from simple_smartsheet.models.column import Column, ColumnSchema
from simple_smartsheet.models.row import Row, RowSchema, _RowBase
from simple_smartsheet.models.extra import Result

logger = logging.getLogger(__name__)


class UserSettingsSchema(Schema):
    critical_path_enabled = fields.Bool(data_key="criticalPathEnabled")
    display_summary_tasks = fields.Bool(data_key="displaySummaryTasks")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class UserSettings(Object):
    critical_path_enabled: bool
    display_summary_tasks: bool


class UserPermissionsSchema(Schema):
    summary_permissions = fields.Str(data_key="summaryPermissions")


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class UserPermissions(Object):
    summary_permissions: str


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
    user_permissions = fields.Nested(UserPermissionsSchema, data_key="userPermissions")
    has_summary_fields = fields.Bool(data_key="hasSummaryFields")

    columns = fields.List(fields.Nested(ColumnSchema))
    rows = fields.List(fields.Nested(RowSchema))
    workspace = fields.Nested(WorkspaceSchema)

    class Meta:
        unknown = utils.get_unknown_field_handling(config.IS_DEVELOPMENT)
        ordered = True

    @pre_load
    def update_context(self, data, many: bool, **kwargs):
        self.context["column_id_to_type"] = {}
        return data


RowT = TypeVar("RowT", bound=_RowBase[Any])
ColumnT = TypeVar("ColumnT", bound=Column)


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class _SheetBase(CoreObject, Generic[RowT, ColumnT]):
    """Represents Smartsheet Sheet object

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#sheets

    Extra attributes:
        indexes: contains all built indices
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
    user_permissions: Optional[UserPermissions] = None
    has_summary_fields: Optional[bool] = None

    columns: List[ColumnT] = attr.Factory(list)
    rows: List[RowT] = attr.Factory(list)
    workspace: Optional[Workspace] = None

    _row_num_to_row: Dict[int, RowT] = attr.ib(attr.Factory(dict), init=False)
    _row_id_to_row: Dict[int, RowT] = attr.ib(attr.Factory(dict), init=False)
    _column_title_to_column: Dict[str, ColumnT] = attr.ib(
        attr.Factory(dict), init=False
    )
    _column_id_to_column: Dict[int, ColumnT] = attr.ib(attr.Factory(dict), init=False)
    indexes: IndexesType = attr.ib(attr.Factory(dict), init=False)

    _schema: ClassVar[Type[SheetSchema]] = SheetSchema

    def __attrs_post_init__(self) -> None:
        self._update_column_lookup()
        self._update_row_cell_lookup()

    def _update_column_lookup(self) -> None:
        self._column_title_to_column.clear()
        self._column_id_to_column.clear()

        for column in self.columns:
            column_id = column._id
            if column_id is None:
                continue
            self._column_id_to_column[column_id] = column

            column_title = column.title
            if column_title is None:
                continue
            if column_title in self._column_title_to_column:
                logger.info(
                    "Column with the title %s is already present in the index",
                    column_title,
                )
            self._column_title_to_column[column_title] = column

    def _update_row_cell_lookup(self) -> None:
        self._row_num_to_row.clear()
        self._row_id_to_row.clear()

        for row in self.rows:
            if row.num:
                self._row_num_to_row[row.num] = row

            if row.id:
                self._row_id_to_row[row.id] = row

            row._update_cell_lookup(self)

    def build_index(self, indexes: List[IndexKeysDict]) -> None:
        for index in indexes:
            columns = index["columns"]
            unique = index["unique"]
            self.indexes[columns] = {"index": {}, "unique": unique}

        for row in self.rows:
            row._update_index(self)

    def get_row(
        self,
        row_num: Optional[int] = None,
        row_id: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> Optional[RowT]:
        """Returns Row object by row number or ID

        Either row_num or row_id must be provided

        Args:
            row_num: row number
            row_id: row id
            filter: a dictionary with column title to value
        mappings in the same order as index was built. Index must be unique.

        Returns:
            Row object
        """
        if row_num is not None:
            return self._row_num_to_row.get(row_num)
        elif row_id is not None:
            return self._row_id_to_row.get(row_id)
        elif filter is not None:
            columns, query = zip(*sorted(filter.items()))
            index_dict = self.indexes.get(columns)
            if index_dict is None:
                raise exceptions.SmartsheetIndexNotFound(
                    f"Index {columns} is not found, "
                    f"build it first with build_index method"
                )

            unique = index_dict["unique"]
            if not unique:
                raise exceptions.SmartsheetIndexNotUnique(
                    f"Index {columns} is non-unique and lookup will potentially "
                    "return multiple rows, use get_rows method instead"
                )
            index = cast(Dict[Tuple[Any, ...], RowT], index_dict["index"])
            return index[query]
        else:
            raise ValueError("Either row_num or row_id argument should be provided")

    def get_rows(self, filter: Dict[str, Any]) -> List[RowT]:
        """Returns Row objects by index query

        Args:
            filter: a dictionary or ordered dictionary with column title to value
        mappings in the same order as index was built. Index must be non-unique.

        Returns:
            Row object
        """
        columns, query = zip(*sorted(filter.items()))
        index_dict = self.indexes.get(columns)
        if index_dict is None:
            raise exceptions.SmartsheetIndexNotFound(
                f"Index {columns} is not found, "
                f"build it first with build_index method"
            )

        unique = index_dict["unique"]
        if unique:
            unique_index = cast(Dict[Tuple[Any, ...], RowT], index_dict["index"])
            result = unique_index.get(query)
            if result is not None:
                return [result]
            else:
                return []
        else:
            non_unique_index = cast(
                Dict[Tuple[Any, ...], List[RowT]], index_dict["index"]
            )
            return non_unique_index.get(query, [])

    def get_column(
        self, column_title: Optional[str] = None, column_id: Optional[int] = None
    ) -> ColumnT:
        """Returns Column object by column title or ID

        Either column_title or column_id must be provided

        Args:
            column_title: column title (case-sensitive)
            column_id: column id

        Returns:
            Column object
        """
        if column_title is not None:
            return self._column_title_to_column[column_title]
        elif column_id is not None:
            return self._column_id_to_column[column_id]
        else:
            raise ValueError(
                "Either column_title or column_id argument should be provided"
            )

    def as_list(self) -> List[Dict[str, Union[float, str, datetime, None]]]:
        """Returns a list of dictionaries with column titles and cell values"""
        return [row.as_dict() for row in self.rows]


@attr.s(auto_attribs=True, repr=False, kw_only=True)
class _Sheet(_SheetBase[Row, Column]):
    columns: List[Column] = cast(List[Column], attr.Factory(list))
    rows: List[Row] = attr.Factory(list)

    def make_cell(self, column_title: str, field_value: Any) -> Cell:
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

    def make_cells(self, fields: Dict[str, Any]) -> List[Cell]:
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


class Sheet(_Sheet):
    """Represents Smartsheet Sheet object with additional synchronous methods

    Additional details about fields can be found here:
    http://smartsheet-platform.github.io/api-docs/#sheets

    Extra attributes:
        _row_тum_to_row: mapping of row number to Row object
        _row_id_to_row: mapping of row id to Row object
        _column_title_to_column: mapping of column title to Column object
        _column_id_to_column: mapping of column id to Column object
        _schema: reference to SheetSchema
    """

    # TODO: remove the class in 0.4.0
    def add_rows(self, rows: Sequence[Row]) -> Result:
        """Adds several rows to the Sheet (deprecated).

        Every row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            rows: sequence of Row objects

        Returns:
            Result object
        """
        msg = (
            "Method 'add_rows' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.add_rows instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        elif self.id is None:
            raise ValueError("The attribute 'id' must not be None")
        else:
            return self.smartsheet.sheets.add_rows(self.id, rows)

    def add_row(self, row: Row) -> Result:
        """Adds a single row to the Sheeet (deprecated).

        A row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            row: Row object

        Returns:
            Result object
        """
        msg = (
            "Method 'add_row' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.add_row instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        elif self.id is None:
            raise ValueError("The attribute 'id' must not be None")
        else:
            return self.smartsheet.sheets.add_row(self.id, row)

    def update_rows(self, rows: Sequence[Row]) -> Result:
        """Updates several rows in the Sheet (deprecated).

        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            rows: sequence of Row objects

        Returns:
            Result object
        """
        msg = (
            "Method 'update_rows' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.update_rows instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        elif self.id is None:
            raise ValueError("The attribute 'id' must not be None")
        else:
            return self.smartsheet.sheets.update_rows(self.id, rows)

    def update_row(self, row: Row) -> Result:
        """Updates a single row in the Sheet (deprecated).

        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            row: Row object

        Returns:
            Result object
        """
        msg = (
            "Method 'update_row' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.update_row instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        elif self.id is None:
            raise ValueError("The attribute 'id' must not be None")
        else:
            return self.smartsheet.sheets.update_row(self.id, row)

    def delete_rows(self, row_ids: Sequence[int]) -> Result:
        """Deletes several rows in the Sheet (deprecated).

        Rows are identified by ids.

        Args:
            row_ids: sequence of row ids

        Returns:
            Result object
        """
        msg = (
            "Method 'delete_rows' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.delete_rows instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        elif self.id is None:
            raise ValueError("The attribute 'id' must not be None")
        else:
            return self.smartsheet.sheets.delete_rows(self.id, row_ids)

    def delete_row(self, row_id: int) -> Result:
        """Deletes a single row in the Sheet specified by ID (deprecated).

        Args:
            row_id: Row id

        Returns:
            Result object
        """
        msg = (
            "Method 'delete_row' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.delete_row instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        elif self.id is None:
            raise ValueError("The attribute 'id' must not be None")
        else:
            return self.smartsheet.sheets.delete_row(self.id, row_id)

    def sort_rows(self, order: List[Dict[str, Any]]) -> "Sheet":
        """Sorts rows in the sheet with the specified order (deprecated)

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
        msg = (
            "Method 'sort_rows' has been deprecated and will be "
            "removed in the next version, use smartsheet.sheets.sort_rows instead"
        )
        warnings.warn(msg, DeprecationWarning)
        if not isinstance(self.smartsheet, smartsheet.Smartsheet):
            raise ValueError(
                f"The attribute 'smartsheet' is of type {type(self.smartsheet)}, "
                f"must be 'Smartsheet'"
            )
        else:
            return self.smartsheet.sheets.sort_rows(self, order)


class SheetCRUDMixin(CRUDAttrs):
    base_url = "/sheets"

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

    update_include_fields = ("name",)

    _rows_include_fields = [
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
    ]
    _rows_endpoint = "/sheets/{sheet_id}/rows"
    _sort_rows_endpoint: ClassVar[str] = "/sheets/{sheet.id}/sort"

    @staticmethod
    def _sheet_id(sheet_id: Union[Sheet, int]):
        if isinstance(sheet_id, int):
            return sheet_id
        elif isinstance(sheet_id, Sheet):
            msg = (
                "Please provide ID of a sheet as the first "
                "argument instead of a Sheet object."
            )
            warnings.warn(msg, DeprecationWarning)
            return sheet_id.id
        else:
            raise ValueError(f"Unknown type {type(sheet_id)} for sheet_id")

    @staticmethod
    def _add_or_update_row_data(row: Row, schema: RowSchema):
        updated_row = row.copy(deep=False)
        updated_row.cells = [
            cell
            for cell in row.cells
            if cell.value is not None or cell.formula is not None
        ]
        result = schema.dump(updated_row)
        return result

    @property
    def _add_row_schema(self) -> RowSchema:
        return RowSchema(only=self._rows_include_fields + ["sibling_id"])

    @property
    def _update_row_schema(self) -> RowSchema:
        return RowSchema(only=self._rows_include_fields + ["id"])

    def _add_rows_data(self, rows: Sequence[Row]) -> List[Dict[str, Any]]:
        data = []
        schema = RowSchema(only=self._rows_include_fields + ["sibling_id"])
        for row in rows:
            new_row = row.copy(deep=False)
            new_row.cells = [
                cell
                for cell in row.cells
                if cell.value is not None or cell.formula is not None
            ]
            data.append(schema.dump(new_row))
        return data

    def _update_rows_data(self, rows: Sequence[Row]) -> List[Dict[str, Any]]:
        data = []
        schema = RowSchema(only=self._rows_include_fields + ["id"])
        for row in rows:
            new_row = row.copy(deep=False)
            new_row.cells = [
                cell
                for cell in row.cells
                if cell.value is not None or cell.formula is not None
            ]
            data.append(schema.dump(new_row))
        return data

    @staticmethod
    def _delete_rows_params(row_ids: Sequence[int]) -> Dict[str, str]:
        result = {"ids": ",".join(str(row_id) for row_id in row_ids)}
        return result

    @staticmethod
    def _sort_rows_data(sheet: Sheet, order: List[Dict[str, Any]]) -> Dict[str, Any]:
        # TODO: add validation schema for sorting order
        normalized_order = []
        for item in order:
            normalized_item = {}
            if "column_id" in item:
                normalized_item["columnId"] = item["column_id"]
            elif "column_title" in item:
                column_title = item["column_title"]
                column = sheet.get_column(column_title)
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
        return data


class SheetCRUD(SheetCRUDMixin, CRUD[Sheet]):
    factory = Sheet

    def add_rows(self, sheet_id: int, rows: Sequence[Row]) -> Result:
        """Adds several rows to the sheet.

        Every row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            sheet_id: ID of the sheet where rows should be added to
            rows: sequence of Row objects

        Returns:
            Result object
        """
        data = [self._add_or_update_row_data(row, self._add_row_schema) for row in rows]
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = self.smartsheet._post(endpoint, data=data)
        return result

    def add_row(self, sheet_id: int, row: Row) -> Result:
        """Adds a single row to the Sheet.

        A row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            sheet_id: ID of the sheet where a row should be added to
            row: Row object

        Returns:
            Result object
        """
        data = self._add_or_update_row_data(row, self._add_row_schema)
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = self.smartsheet._post(endpoint, data=data)
        return result

    def update_rows(self, sheet_id: int, rows: Sequence[Row]) -> Result:
        """Updates several rows in the Sheet.

        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            sheet_id: ID of the sheet where rows should be updated
            rows: sequence of Row objects

        Returns:
            Result object
        """
        data = [
            self._add_or_update_row_data(row, self._update_row_schema) for row in rows
        ]
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = self.smartsheet._put(endpoint, data=data)
        return result

    def update_row(self, sheet_id: int, row: Row) -> Result:
        """Updates a single row in the Sheet.

        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            sheet_id: ID of the sheet where a row should be updated
            row: Row object

        Returns:
            Result object
        """
        data = self._add_or_update_row_data(row, self._update_row_schema)
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = self.smartsheet._put(endpoint, data=data)
        return result

    def delete_rows(self, sheet_id: int, row_ids: Sequence[int]) -> Result:
        """Deletes several rows in the Sheet.

        Rows are identified by ids.

        Args:
            sheet_id: ID of the sheet where rows should be deleted from
            row_ids: sequence of row ids

        Returns:
            Result object
        """
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        params = self._delete_rows_params(row_ids)
        result = self.smartsheet._delete(endpoint, params=params)
        return result

    def delete_row(self, sheet_id: int, row_id: int) -> Result:
        """Deletes a single row in the Sheet specified by ID.

        Args:
            sheet_id: ID of the sheet where a row should be deleted from
            row_id: Row id

        Returns:
            Result object
        """
        return self.delete_rows(sheet_id, [row_id])

    def sort_rows(self, sheet: Sheet, order: List[Dict[str, Any]]) -> "Sheet":
        """Sorts rows in the sheet with the specified order.

        Args:
            sheet: Sheet object where the rows should be sorted
            order: List of dictionaries containing column_title or column_id and
                (optional) descending bool (default is ascending). Example:
                [
                    {"column_title": "Birth date", "descending": True},
                    {"column_title": "Full Name"}
                ]

        Returns:
            Sheet object
        """
        data = self._sort_rows_data(sheet, order)
        endpoint = self._sort_rows_endpoint.format(sheet=sheet)
        response = self.smartsheet._post(endpoint, data, result_obj=False)
        updated_sheet = Sheet.load(cast(Dict[str, Any], response))
        updated_sheet.smartsheet = self.smartsheet  # TODO: remove in later release
        return updated_sheet


class SheetAsyncCRUD(SheetCRUDMixin, AsyncCRUD[Sheet]):
    factory = Sheet

    async def add_rows(self, sheet_id: int, rows: Sequence[Row]) -> Result:
        """Adds several rows to the sheet asynchronously.

        Every row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            sheet_id: ID of the sheet where rows should be added to
            rows: sequence of Row objects

        Returns:
            Result object
        """
        data = [self._add_or_update_row_data(row, self._add_row_schema) for row in rows]
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = await self.smartsheet._post(endpoint, data=data)
        return cast(Result, result)

    async def add_row(self, sheet_id: int, row: Row) -> Result:
        """Adds a single row to the Sheet asynchronously.

        A row must have either location-specifier attributes or row number set
        More details: http://smartsheet-platform.github.io/api-docs/#add-rows

        Args:
            sheet_id: ID of the sheet where a row should be added to
            row: Row object

        Returns:
            Result object
        """
        data = self._add_or_update_row_data(row, self._add_row_schema)
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = await self.smartsheet._post(endpoint, data=data)
        return cast(Result, result)

    async def update_rows(self, sheet_id: int, rows: Sequence[Row]) -> Result:
        """Updates several rows in the Sheet asynchronously.

        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            sheet_id: ID of the sheet where rows should be updated
            rows: sequence of Row objects

        Returns:
            Result object
        """
        data = [
            self._add_or_update_row_data(row, self._update_row_schema) for row in rows
        ]
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = await self.smartsheet._put(endpoint, data=data)
        return cast(Result, result)

    async def update_row(self, sheet_id: int, row: Row) -> Result:
        """Updates a single row in the Sheet asynchronously.

        More details: http://smartsheet-platform.github.io/api-docs/#update-rows

        Args:
            sheet_id: ID of the sheet where a row should be updated
            row: Row object

        Returns:
            Result object
        """
        data = self._add_or_update_row_data(row, self._update_row_schema)
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        result = await self.smartsheet._put(endpoint, data=data)
        return cast(Result, result)

    async def delete_rows(self, sheet_id: int, row_ids: Sequence[int]) -> Result:
        """Deletes several rows in the Sheet asynchronously.

        Rows are identified by ids.

        Args:
            sheet_id: ID of the sheet where rows should be deleted from
            row_ids: sequence of row ids

        Returns:
            Result object
        """
        endpoint = self._rows_endpoint.format(sheet_id=self._sheet_id(sheet_id))
        params = self._delete_rows_params(row_ids)
        result = await self.smartsheet._delete(endpoint, params=params)
        return result

    async def delete_row(self, sheet_id: int, row_id: int) -> Result:
        """Deletes a single row in the Sheet specified by ID asynchronously.

        Args:
            sheet_id: ID of the sheet where a row should be deleted from
            row_id: Row id

        Returns:
            Result object
        """
        return await self.delete_rows(sheet_id, [row_id])

    async def sort_rows(self, sheet: Sheet, order: List[Dict[str, Any]]) -> "Sheet":
        """Sorts rows in the sheet with the specified order asynchronously.

        Args:
            sheet: the sheet where the rows should be sorted
            order: List of dictionaries containing column_title or column_id and
                (optional) descending bool (default is ascending). Example:
                [
                    {"column_title": "Birth date", "descending": True},
                    {"column_title": "Full Name"}
                ]

        Returns:
            Sheet object
        """
        data = self._sort_rows_data(sheet, order)
        endpoint = self._sort_rows_endpoint.format(sheet=sheet)
        response = await self.smartsheet._post(endpoint, data, result_obj=False)
        sheet = sheet.load(cast(Dict[str, Any], response))
        sheet.smartsheet = self.smartsheet  # TODO: remove in later release
        return sheet
