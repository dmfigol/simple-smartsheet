import os
from datetime import date
from pprint import pprint

from simple_smartsheet import Smartsheet
from simple_smartsheet.models import Sheet, Column, Row, Cell, ColumnType


TOKEN = os.getenv("SMARTSHEET_API_TOKEN")
SHEET_NAME = "[TEST] My New Sheet"


def main() -> None:
    with Smartsheet(TOKEN) as smartsheet:
        # retrieve a list of sheets (limited set of attributes)
        sheets = smartsheet.sheets.list()
        pprint(sheets)

        # delete the test sheet if already exists
        for sheet in sheets:
            if sheet.name == SHEET_NAME:
                smartsheet.sheets.delete(id=sheet.id)

        # create a new Sheet
        new_sheet_skeleton = Sheet(
            name=SHEET_NAME,
            columns=[
                Column(primary=True, title="Full Name", type=ColumnType.TEXT_NUMBER),
                Column(title="Number of read books", type=ColumnType.TEXT_NUMBER),
                Column(title="Birth date", type=ColumnType.DATE),
                Column(title="Library member", type=ColumnType.CHECKBOX),
            ],
        )

        # print the sheet object attributes used by the Smartsheet API (camelCase)
        pprint(new_sheet_skeleton.dump())

        # add the sheet via API
        result = smartsheet.sheets.create(new_sheet_skeleton)
        sheet = result.obj
        print(f"ID of the created sheet is {sheet.id!r}")

        # retrieve a sheet by name
        # this object is exactly the same as result.obj
        sheet = smartsheet.sheets.get(SHEET_NAME)

        # get columns details by column title (case-sensitive)
        full_name_column = sheet.get_column("Full Name")
        pprint(full_name_column.__dict__)
        num_books_column = sheet.get_column("Number of read books")
        pprint(num_books_column.__dict__)

        # add rows (cells are created using different ways)
        # second way is the easiest
        new_rows = [
            Row(
                to_top=True,
                cells=[
                    Cell(column_id=full_name_column.id, value="Alice Smith"),
                    Cell(column_id=num_books_column.id, value=5),
                ],
            ),
            Row(
                to_top=True,
                cells=sheet.make_cells(
                    {"Full Name": "Bob Lee", "Number of read books": 2}
                ),
            ),
            Row(
                to_top=True,
                cells=[
                    sheet.make_cell("Full Name", "Charlie Brown"),
                    sheet.make_cell("Number of read books", 1),
                    sheet.make_cell("Birth date", date(1990, 1, 1)),
                ],
            ),
        ]
        smartsheet.sheets.add_rows(sheet.id, new_rows)

        # sort rows by column "Full Name" descending / returns updated sheet
        sheet = smartsheet.sheets.sort_rows(
            sheet, [{"column_title": "Full Name", "descending": True}]
        )

        print("\nSheet after adding rows:")
        # print a list of dictionaries containing column titles and values for each row
        pprint(sheet.as_list())

        # get a specific cell and updating it:
        row_id_to_delete = None
        rows_to_update = []
        for row in sheet.rows:
            full_name = row.get_cell("Full Name").value
            num_books = row.get_cell("Number of read books").value
            print(f"{full_name} has read {num_books} books")
            if full_name.startswith("Charlie"):
                updated_row = Row(
                    id=row.id, cells=[sheet.make_cell("Number of read books", 15)]
                )
                rows_to_update.append(updated_row)
            elif full_name.startswith("Bob"):
                row_id_to_delete = row.id  # used later

        # update rows
        smartsheet.sheets.update_rows(sheet.id, rows_to_update)
        # or a single row
        # smartsheet.sheets.update_row(sheet.id, rows_to_update[0])

        # get an updated sheet
        sheet = smartsheet.sheets.get(id=sheet.id)
        print("\nSheet after updating rows:")
        pprint(sheet.as_list())

        # delete a row
        smartsheet.sheets.delete_row(sheet.id, row_id_to_delete)

        # get an updated sheet
        sheet = smartsheet.sheets.get(id=sheet.id)
        print("\nSheet after deleting rows:")
        pprint(sheet.as_list())

        # delete a sheet by name
        smartsheet.sheets.delete(SHEET_NAME)
        sheets = smartsheet.sheets.list()
        pprint(sheets)


if __name__ == "__main__":
    if TOKEN:
        main()
