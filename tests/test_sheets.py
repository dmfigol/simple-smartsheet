from datetime import date

import pytest
from vcr import VCR
from typing import List, Dict, Any, cast

from simple_smartsheet import Smartsheet, AsyncSmartsheet
from simple_smartsheet import exceptions
from simple_smartsheet.models import Column, Sheet, Row, ColumnType


@pytest.fixture
def new_sheet(placeholder_sheet) -> Sheet:
    placeholder_sheet.name = "[TEST] New Sheet"
    return placeholder_sheet


@pytest.fixture
def sheet_to_update(placeholder_sheet) -> Sheet:
    placeholder_sheet.name = "[TEST] Sheet To Update"
    return placeholder_sheet


@pytest.fixture
def sheet_to_delete(placeholder_sheet) -> Sheet:
    placeholder_sheet.name = "[TEST] Sheet To Delete"
    return placeholder_sheet


def create_sheet_with_rows(smartsheet, target_sheet, rows_data) -> Sheet:
    result = smartsheet.sheets.create(target_sheet)
    new_sheet = cast(Sheet, result.obj)
    rows = [
        Row(to_top=True, cells=new_sheet.make_cells(row_data)) for row_data in rows_data
    ]
    smartsheet.sheets.add_rows(result.obj.id, rows)
    return new_sheet


class TestListSheets:
    @pytest.mark.vcr("list_sheets.yaml")
    def test_list_sheets(self, smartsheet):
        sheets = smartsheet.sheets.list()
        assert len(sheets) > 0
        assert all(isinstance(sheet, Sheet) for sheet in sheets)
        assert any(sheet.name.startswith("[TEST]") for sheet in sheets)

    @pytest.mark.asyncio
    @pytest.mark.vcr("list_sheets_async.yaml")
    async def test_list_sheets_async(self, async_smartsheet):
        sheets = await async_smartsheet.sheets.list()
        assert len(sheets) > 0
        assert all(isinstance(sheet, Sheet) for sheet in sheets)
        assert any(sheet.name.startswith("[TEST]") for sheet in sheets)


class TestGetSheet:
    INDEXES = [
        {"columns": ("Company",), "unique": False},
        {"columns": ("Company", "Full Name"), "unique": True},
        {"columns": ("Email address",), "unique": True},
    ]
    SHEET_NAME = "[TEST] Read-only Sheet"

    @pytest.mark.vcr("get_sheet.yaml")
    def test_get_sheet(self, smartsheet):
        sheet = smartsheet.sheets.get(name=self.SHEET_NAME)
        self.check_sheet(sheet)

    @pytest.mark.asyncio
    @pytest.mark.vcr("get_sheet_async.yaml")
    async def test_get_sheet_async(self, async_smartsheet):
        sheet = await async_smartsheet.sheets.get(name=self.SHEET_NAME)
        self.check_sheet(sheet)

    def check_sheet(self, sheet):
        assert sheet.name == self.SHEET_NAME
        assert sheet.columns
        assert any(
            row.get_cell("Email address").value == "bob.lee@acme.com"
            for row in sheet.rows
        )
        assert any(
            "nornir" in row.get_cell("Maintains").get_value()
            and row.get_cell("Full Name").value == "Charlie Brown"
            for row in sheet.rows
        )
        self.check_indexes(sheet)

    def check_indexes(self, sheet):
        sheet.build_index(self.INDEXES)
        row = sheet.get_row(filter={"Email address": "charlie.brown@acme.com"})
        assert row.get_cell("Email address").value == "charlie.brown@acme.com"
        assert row.get_cell("Full Name").value == "Charlie Brown"
        assert row.get_cell("Birth date").value == date(1990, 1, 1)
        assert not row.get_cell("Married").value
        assert row.get_cell("Number of children").value == 1.0

        rows = sheet.get_rows(filter={"Company": "ACME"})
        assert len(rows) == 2
        for row in rows:
            assert row.get_cell("Company").value == "ACME"


class TestCreateSheet:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, custom_vcr, smartsheet, new_sheet):
        yield
        with custom_vcr.use_cassette("test_sheets/create_sheet_teardown.yaml"):
            sheets = smartsheet.sheets.list()
            for sheet in sheets:
                if sheet.name == new_sheet.name:
                    smartsheet.sheets.delete(id=sheet.id)

    @pytest.mark.vcr("create_sheet.yaml")
    def test_create_sheet(self, smartsheet, new_sheet):
        result = smartsheet.sheets.create(new_sheet)
        assert result.message == "SUCCESS"
        assert result.obj.id
        assert result.obj.name == new_sheet.name

    @pytest.mark.asyncio
    @pytest.mark.vcr("create_sheet_async.yaml")
    async def test_create_sheet_async(self, async_smartsheet, new_sheet):
        result = await async_smartsheet.sheets.create(new_sheet)
        assert result.message == "SUCCESS"
        assert result.obj.id
        assert result.obj.name == new_sheet.name

    @pytest.mark.vcr("create_sheet_error.yaml")
    def test_create_sheet_error(self, smartsheet, new_sheet):
        new_sheet.columns.append(Column(title="Full Name", type=ColumnType.TEXT_NUMBER))
        try:
            smartsheet.sheets.create(new_sheet)
            pytest.fail("This test must always raise SmartsheetHTTPClientError")
        except exceptions.SmartsheetHTTPClientError as e:
            assert e.status_code == 400
            assert e.error.error_code == 1056
            assert e.error.message == "Column titles must be unique."
        else:
            raise

    @pytest.mark.asyncio
    @pytest.mark.vcr("create_sheet_error_async.yaml")
    async def test_create_sheet_error_async(self, async_smartsheet, new_sheet):
        new_sheet.columns.append(Column(title="Full Name", type=ColumnType.TEXT_NUMBER))
        try:
            await async_smartsheet.sheets.create(new_sheet)
            pytest.fail(
                "This test must always raise an exception SmartsheetHTTPClientError"
            )
        except exceptions.SmartsheetHTTPClientError as e:
            assert e.status_code == 400
            assert e.error.error_code == 1056
            assert e.error.message == "Column titles must be unique."
        else:
            raise


class TestDeleteSheet:
    @pytest.fixture(autouse=True)
    def setup_teardown(self, custom_vcr, smartsheet, sheet_to_delete):
        with custom_vcr.use_cassette("test_sheets/delete_sheet_setup.yaml"):
            sheets = smartsheet.sheets.list()
            if not any(sheet.name == sheet_to_delete.name for sheet in sheets):
                smartsheet.sheets.create(sheet_to_delete)

    @pytest.mark.vcr("delete_sheet.yaml")
    def test_delete_sheet(self, smartsheet, sheet_to_delete):
        result = smartsheet.sheets.delete(name=sheet_to_delete.name)
        assert result.message == "SUCCESS"

    @pytest.mark.asyncio
    @pytest.mark.vcr("delete_sheet_async.yaml")
    async def test_delete_sheet_name_async(self, async_smartsheet, sheet_to_delete):
        result = await async_smartsheet.sheets.delete(name=sheet_to_delete.name)
        assert result.message == "SUCCESS"


class TestUpdateSheet:
    @pytest.fixture(autouse=True)
    def setup_teardown(
        self,
        custom_vcr: VCR,
        smartsheet: Smartsheet,
        sheet_to_update: Sheet,
        rows_data: List[Dict[str, Any]],
    ) -> None:
        with custom_vcr.use_cassette("test_sheets/update_sheet_setup.yaml"):
            new_sheet = create_sheet_with_rows(smartsheet, sheet_to_update, rows_data)
        yield
        with custom_vcr.use_cassette("test_sheets/update_sheet_teardown.yaml"):
            smartsheet.sheets.delete(id=new_sheet.id)

    @pytest.mark.vcr("update_sheet_name.yaml")
    def test_update_sheet_name(
        self, smartsheet: Smartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        new_name = "[TEST] Updated Sheet"
        sheet.name = new_name
        result = smartsheet.sheets.update(sheet)
        assert result.message == "SUCCESS"
        assert result.obj.name == new_name

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_name_async.yaml")
    async def test_update_sheet_name_async(
        self, async_smartsheet: AsyncSmartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        new_name = "[TEST] Updated Sheet"
        sheet.name = new_name
        result = await async_smartsheet.sheets.update(sheet)
        assert result.message == "SUCCESS"
        assert result.obj.name == new_name

    @pytest.mark.vcr("update_sheet_add_row.yaml")
    def test_sheet_add_row(
        self,
        smartsheet: Smartsheet,
        sheet_to_update: Sheet,
        additional_row_data: Dict[str, Any],
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        new_row = Row(cells=sheet.make_cells(additional_row_data))
        result = smartsheet.sheets.add_row(sheet.id, new_row)
        assert result.message == "SUCCESS"

        updated_sheet = smartsheet.sheets.get(id=sheet.id)
        assert len(updated_sheet.rows) == 4
        assert (
            updated_sheet.rows[-1].get_cell("Email address").value
            == "david.ward@globex.com"
        )

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_add_row_async.yaml")
    async def test_sheet_add_row_async(
        self,
        async_smartsheet: AsyncSmartsheet,
        sheet_to_update: Sheet,
        additional_row_data: Dict[str, Any],
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        new_row = Row(cells=sheet.make_cells(additional_row_data))
        result = await async_smartsheet.sheets.add_row(sheet.id, new_row)
        assert result.message == "SUCCESS"

        updated_sheet = await async_smartsheet.sheets.get(id=sheet.id)
        assert len(updated_sheet.rows) == 4
        assert (
            updated_sheet.rows[-1].get_cell("Email address").value
            == "david.ward@globex.com"
        )

    @pytest.mark.vcr("update_sheet_add_rows.yaml")
    def test_sheet_add_rows(
        self,
        smartsheet: Smartsheet,
        sheet_to_update: Sheet,
        additional_rows_data: List[Dict[str, Any]],
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        new_rows = [
            Row(to_bottom=True, cells=sheet.make_cells(row_data))
            for row_data in additional_rows_data
        ]
        result = smartsheet.sheets.add_rows(sheet.id, new_rows)
        assert result.message == "SUCCESS"

        updated_sheet = smartsheet.sheets.get(id=sheet.id)
        assert len(updated_sheet.rows) == 5
        assert (
            updated_sheet.rows[-1].get_cell("Email address").value
            == "elizabeth.warner@acme.com"
        )

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_add_rows_async.yaml")
    async def test_sheet_add_rows_async(
        self,
        async_smartsheet: AsyncSmartsheet,
        sheet_to_update: Sheet,
        additional_rows_data: List[Dict[str, Any]],
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        new_rows = [
            Row(to_bottom=True, cells=sheet.make_cells(row_data))
            for row_data in additional_rows_data
        ]
        result = await async_smartsheet.sheets.add_rows(sheet.id, new_rows)
        assert result.message == "SUCCESS"

        updated_sheet = await async_smartsheet.sheets.get(id=sheet.id)
        assert len(updated_sheet.rows) == 5
        assert (
            updated_sheet.rows[-1].get_cell("Email address").value
            == "elizabeth.warner@acme.com"
        )

    @pytest.mark.vcr("update_sheet_row.yaml")
    def test_sheet_update_row(
        self, smartsheet: Smartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})

        if row is None:
            pytest.fail("The row was not found")

        row.cells = sheet.make_cells({"Full Name": "Alice Han", "Married": True})
        result = smartsheet.sheets.update_row(sheet.id, row)
        assert result.message == "SUCCESS"

        updated_sheet = smartsheet.sheets.get(id=sheet.id)
        updated_row = updated_sheet.get_row(row_id=row.id)
        assert updated_row.get_cell("Full Name").value == "Alice Han"
        assert updated_row.get_cell("Married").value is True

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_row_async.yaml")
    async def test_sheet_update_row_async(
        self, async_smartsheet: AsyncSmartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})

        if row is None:
            pytest.fail("The row was not found")

        row.cells = sheet.make_cells({"Full Name": "Alice Han", "Married": True})
        result = await async_smartsheet.sheets.update_row(sheet.id, row)
        assert result.message == "SUCCESS"

        updated_sheet = await async_smartsheet.sheets.get(id=sheet.id)
        updated_row = updated_sheet.get_row(row_id=row.id)
        assert updated_row.get_cell("Full Name").value == "Alice Han"
        assert updated_row.get_cell("Married").value is True

    @pytest.mark.vcr("update_sheet_rows.yaml")
    def test_sheet_update_rows(
        self, smartsheet: Smartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row1 = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})
        row2 = sheet.get_row(filter={"Email address": "bob.lee@acme.com"})

        if row1 is None or row2 is None:
            pytest.fail(
                "At least one of the rows with specified parameters was not found"
            )

        row1.cells = sheet.make_cells(
            {"Full Name": "Alice Han", "Birth date": date(1989, 12, 31)}
        )
        row2.cells = sheet.make_cells({"Company": "Globex", "Number of children": ""})
        result = smartsheet.sheets.update_rows(sheet.id, [row1, row2])
        assert result.message == "SUCCESS"

        updated_sheet = smartsheet.sheets.get(id=sheet.id)
        updated_row1 = updated_sheet.get_row(row_id=row1.id)
        updated_row2 = updated_sheet.get_row(row_id=row2.id)
        assert updated_row1.get_cell("Full Name").value == "Alice Han"
        assert updated_row1.get_cell("Birth date").value == date(1989, 12, 31)
        assert updated_row2.get_cell("Company").value == "Globex"
        assert updated_row2.get_cell("Number of children").value is None

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_rows_async.yaml")
    async def test_sheet_update_rows_async(
        self, async_smartsheet: AsyncSmartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row1 = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})
        row2 = sheet.get_row(filter={"Email address": "bob.lee@acme.com"})

        if row1 is None or row2 is None:
            pytest.fail(
                "At least one of the rows with specified parameters was not found"
            )

        row1.cells = sheet.make_cells(
            {"Full Name": "Alice Han", "Birth date": date(1989, 12, 31)}
        )
        row2.cells = sheet.make_cells({"Company": "Globex", "Number of children": ""})
        result = await async_smartsheet.sheets.update_rows(sheet.id, [row1, row2])
        assert result.message == "SUCCESS"

        updated_sheet = await async_smartsheet.sheets.get(id=sheet.id)
        updated_row1 = updated_sheet.get_row(row_id=row1.id)
        updated_row2 = updated_sheet.get_row(row_id=row2.id)
        assert updated_row1.get_cell("Full Name").value == "Alice Han"
        assert updated_row1.get_cell("Birth date").value == date(1989, 12, 31)
        assert updated_row2.get_cell("Company").value == "Globex"
        assert updated_row2.get_cell("Number of children").value is None

    @pytest.mark.vcr("update_sheet_delete_row.yaml")
    def test_sheet_delete_row(
        self, smartsheet: Smartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})

        if row is None:
            pytest.fail("The row was not found")

        result = smartsheet.sheets.delete_row(sheet.id, row.id)
        assert result.message == "SUCCESS"

        updated_sheet = smartsheet.sheets.get(id=sheet.id)
        assert updated_sheet.get_row(row_id=row.id) is None
        assert len(updated_sheet.rows) == 2

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_delete_row_async.yaml")
    async def test_sheet_delete_row_async(
        self, async_smartsheet: AsyncSmartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})

        if row is None:
            pytest.fail("The row was not found")

        result = await async_smartsheet.sheets.delete_row(sheet.id, row.id)
        assert result.message == "SUCCESS"

        updated_sheet = await async_smartsheet.sheets.get(id=sheet.id)
        assert updated_sheet.get_row(row_id=row.id) is None
        assert len(updated_sheet.rows) == 2

    @pytest.mark.vcr("update_sheet_delete_rows.yaml")
    def test_sheet_delete_rows(
        self, smartsheet: Smartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row1 = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})
        row2 = sheet.get_row(filter={"Email address": "bob.lee@acme.com"})

        if row1 is None or row2 is None:
            pytest.fail(
                "At least one of the rows with specified parameters was not found"
            )

        result = smartsheet.sheets.delete_rows(sheet.id, [row1.id, row2.id])
        assert result.message == "SUCCESS"

        updated_sheet = smartsheet.sheets.get(id=sheet.id)
        assert updated_sheet.get_row(row_id=row1.id) is None
        assert updated_sheet.get_row(row_id=row2.id) is None
        assert len(updated_sheet.rows) == 1

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_delete_rows_async.yaml")
    async def test_sheet_delete_rows_async(
        self, async_smartsheet: AsyncSmartsheet, sheet_to_update: Sheet
    ) -> None:
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        sheet.build_index([{"columns": ("Email address",), "unique": True}])
        row1 = sheet.get_row(filter={"Email address": "alice.smith@globex.com"})
        row2 = sheet.get_row(filter={"Email address": "bob.lee@acme.com"})

        if row1 is None or row2 is None:
            pytest.fail(
                "At least one of the rows with specified parameters was not found"
            )

        result = await async_smartsheet.sheets.delete_rows(sheet.id, [row1.id, row2.id])
        assert result.message == "SUCCESS"

        updated_sheet = await async_smartsheet.sheets.get(id=sheet.id)
        assert updated_sheet.get_row(row_id=row1.id) is None
        assert updated_sheet.get_row(row_id=row2.id) is None
        assert len(updated_sheet.rows) == 1

    @pytest.mark.vcr("update_sheet_sort_rows.yaml")
    def test_sheet_sort_rows(
        self, smartsheet: Smartsheet, sheet_to_update: Sheet
    ) -> None:
        sort_order = [{"column_title": "Full Name", "descending": False}]
        sheet = smartsheet.sheets.get(name=sheet_to_update.name)
        updated_sheet = smartsheet.sheets.sort_rows(sheet, sort_order)
        assert [row.get_cell("Email address").value for row in updated_sheet.rows] == [
            "alice.smith@globex.com",
            "bob.lee@acme.com",
            "charlie.brown@acme.com",
        ]

    @pytest.mark.asyncio
    @pytest.mark.vcr("update_sheet_sort_rows_async.yaml")
    async def test_sheet_sort_rows_async(
        self, async_smartsheet: AsyncSmartsheet, sheet_to_update: Sheet
    ) -> None:
        sort_order = [{"column_title": "Full Name", "descending": False}]
        sheet = await async_smartsheet.sheets.get(name=sheet_to_update.name)
        updated_sheet = await async_smartsheet.sheets.sort_rows(sheet, sort_order)
        assert [row.get_cell("Email address").value for row in updated_sheet.rows] == [
            "alice.smith@globex.com",
            "bob.lee@acme.com",
            "charlie.brown@acme.com",
        ]
