import os
from datetime import date
from pprint import pprint

from simple_smartsheet import Smartsheet
from simple_smartsheet.models import Sheet, Column, Row, Cell

TOKEN = os.getenv("SMARTSHEET_API_TOKEN")
smartsheet = Smartsheet(TOKEN)

# getting a simplified view of sheets
sheets = smartsheet.sheets.list()
pprint(sheets)

sheet_name = "My New Sheet"
# Delete the test sheet if already exists
for sheet in sheets:
    if sheet.name == sheet_name:
        smartsheet.sheets.delete(sheet_name)

# creating new Sheet
new_sheet = Sheet(
    name=sheet_name,
    columns=[
        Column(primary=True, title="Full Name", type="TEXT_NUMBER"),
        Column(title="Number of read books", type="TEXT_NUMBER"),
        Column(title="Birth date", type="DATE"),
    ],
)

# print the sheet object as a dictionary which will be used in REST API
pprint(new_sheet.dump())

# adding the sheet via API
smartsheet.sheets.create(new_sheet)

# getting a simplified view of sheets
sheets = smartsheet.sheets.list()
pprint(sheets)

# getting the sheet by name
sheet = smartsheet.sheets.get("My New Sheet")

# printing the sheet object attributes
pprint(sheet.__dict__)
# or printing the sheet object as a dictionary which will be used in REST API
pprint(sheet.dump())

# getting columns details by column title (case-sensitive)
full_name_column = sheet.get_column("Full Name")
pprint(full_name_column.__dict__)
num_books_column = sheet.get_column("Number of read books")
pprint(num_books_column.__dict__)

# adding rows (cells created using different ways):
sheet.add_rows(
    [
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
            )
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
)

# sort rows now by column "Full Name" descending / returns updated sheet
sheet = sheet.sort_rows([{"column_title": "Full Name", "descending": True}])

# or getting an updated sheet again
# sheet = smartsheet.sheets.get("My New Sheet")
print("\nSheet after adding rows:")
# all sheet attributes
pprint(sheet.__dict__)
# or just a list of dictionaries containing column titles and values
pprint(sheet.as_list())

# getting a specific cell and updating it:
row_id_to_delete = None
rows_to_update = []
for row in sheet.rows:
    full_name = row.get_cell("Full Name").value
    num_books = row.get_cell("Number of read books").value
    print(f"{full_name} has read {num_books} books")
    if full_name.startswith("Charlie"):
        num_books_cell = row.get_cell("Number of read books")
        num_books_cell.value += 1
        rows_to_update.append(row)
    elif full_name.startswith("Bob"):
        row_id_to_delete = row.id  # used later

# update rows
sheet.update_rows(rows_to_update)
# or a single row
# sheet.update_rows(rows_to_update[0])

# getting an updated sheet
sheet = smartsheet.sheets.get("My New Sheet")
print("\nSheet after updating rows:")
pprint(sheet.as_list())

# deleting row by id
sheet.delete_row(row_id_to_delete)

# getting an updated sheet
sheet = smartsheet.sheets.get("My New Sheet")
print("\nSheet after deleting rows:")
pprint(sheet.as_list())

# deleting Sheet
sheet = smartsheet.sheets.delete('My New Sheet')
sheets = smartsheet.sheets.list()
pprint(sheets)
