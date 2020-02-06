import warnings
from typing import ClassVar, Union, Sequence, List, Dict, Any, cast

from simple_smartsheet import constants
from simple_smartsheet import utils
from simple_smartsheet.crud.base import CRUDAttrs, CRUD, AsyncCRUD
from simple_smartsheet.models import Sheet, Row
from simple_smartsheet.models.extra import Result
from simple_smartsheet.models.row import RowSchema


class SheetCRUDMixin(CRUDAttrs):
    base_url = "/sheets"
    get_params = {"level": "2", "include": "objectValue"}

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
        "cells.object_value",
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
            if cell.value is not None
            or cell.formula is not None
            or cell.object_value is not None
        ]
        result = schema.dump(updated_row.unstructured)
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
            data.append(schema.dump(new_row.unstructured))
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
            data.append(schema.dump(new_row.unstructured))
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
        for row_ids_ in utils.grouper(row_ids, n=constants.MAX_ROWS_TO_DELETE):
            params = self._delete_rows_params(row_ids_)
            result = self.smartsheet._delete(endpoint, params=params)
            if result.message != "SUCCESS":
                raise ValueError(result.message)
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
        return updated_sheet


class AsyncSheetCRUD(SheetCRUDMixin, AsyncCRUD[Sheet]):
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
        for row_ids_ in utils.grouper(row_ids, n=constants.MAX_ROWS_TO_DELETE):
            params = self._delete_rows_params(row_ids_)
            result = await self.smartsheet._delete(endpoint, params=params)
            if result.message != "SUCCESS":
                raise ValueError(result.message)
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
        return sheet
