import logging
from datetime import datetime
from typing import (
    Optional,
    Dict,
    List,
    ClassVar,
    Generic,
    Type,
    TypeVar,
    Tuple,
    Any,
    Union,
    cast,
    TYPE_CHECKING,
)

import attr
from marshmallow import fields, pre_load

from simple_smartsheet import config
from simple_smartsheet import exceptions
from simple_smartsheet import utils
from simple_smartsheet.types import IndexKeysDict, IndexesType
from simple_smartsheet.models.base import Schema, CoreSchema, Object, CoreObject
from simple_smartsheet.models.cell import Cell
from simple_smartsheet.models.column import Column, ColumnSchema, ColumnType
from simple_smartsheet.models.row import Row, RowSchema, _RowBase

if TYPE_CHECKING:
    try:
        import pandas as pd
    except ImportError:
        pass

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
    read_only = fields.Bool(data_key="readOnly")
    dependencies_enabled = fields.Bool(data_key="dependenciesEnabled")
    resource_management_enabled = fields.Bool(data_key="resourceManagementEnabled")
    cell_image_upload_enabled = fields.Bool(data_key="cellImageUploadEnabled")
    user_settings = fields.Nested(UserSettingsSchema, data_key="userSettings")
    user_permissions = fields.Nested(UserPermissionsSchema, data_key="userPermissions")
    has_summary_fields = fields.Bool(data_key="hasSummaryFields")
    is_multi_picklist_enabled = fields.Bool(data_key="isMultiPicklistEnabled")

    columns = fields.List(fields.Nested(ColumnSchema))
    rows = fields.List(fields.Nested(RowSchema))
    workspace = fields.Nested(WorkspaceSchema)

    class Meta:
        unknown = utils.get_unknown_field_handling(config.STRICT_VALIDATION)
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
    read_only: Optional[bool] = None
    dependencies_enabled: Optional[bool] = None
    resource_management_enabled: Optional[bool] = None
    cell_image_upload_enabled: Optional[bool] = None
    user_settings: Optional[UserSettings] = None
    user_permissions: Optional[UserPermissions] = None
    has_summary_fields: Optional[bool] = None
    is_multi_picklist_enabled: Optional[bool] = None

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
class Sheet(_SheetBase[Row, Column]):
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
        if column.type == ColumnType.MULTI_PICKLIST:
            if not column.id:
                raise ValueError(f"Column {column!r} does not have ID")
            cell = Cell.create_multi_picklist(column_id=column.id, values=field_value)
        else:
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

    def as_dataframe(self) -> "pd.DataFrame":
        """Return the sheet as pandas DataFrame

        Columns will includes row id, row number and all columns from the sheet
        Pandas must be installed either separately or as extras:
          `pip install simple-smartsheet[pandas]`
        """
        import pandas as pd

        df = pd.DataFrame([row.as_series() for row in self.rows])
        return df
