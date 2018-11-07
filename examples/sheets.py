from simple_smartsheet import Smartsheet
from simple_smartsheet.models import Sheet, Column, Row, Cell
from pprint import pprint
from decouple import config

TOKEN = config('SMARTSHEET_API_TOKEN')
smartsheet = Smartsheet(TOKEN)

# creating new Sheet
new_sheet = Sheet(
    name="My New Sheet",
    columns=[
        Column(primary=True, title="Full Name", type="TEXT_NUMBER"),
        Column(title="Number of read books", type="TEXT_NUMBER"),
    ]
)

# print the sheet object as a dictionary which will be used in REST API
pprint(new_sheet.dump())

# adding the sheet via API
smartsheet.sheets.create(new_sheet)

# getting a simplified view of sheets
sheets = smartsheet.sheets.list()
pprint(sheets)

# getting the sheet by name
sheet = smartsheet.sheets.get('My New Sheet')

# printing the sheet object attributes
pprint(sheet.__dict__)
# or printing the sheet object as a dictionary which will be used in REST API
pprint(sheet.dump())

# getting columns details by column title (case-sensitive)
full_name_column = sheet.get_column('Full Name')
pprint(full_name_column.__dict__)
num_books_column = sheet.get_column('Number of read books')
pprint(num_books_column.__dict__)

# adding rows:
sheet.add_rows([
    Row(
        to_top=True,
        cells=[
            Cell(column_id=full_name_column.id, value="Alice Smith"),
            Cell(column_id=num_books_column.id, value=5),
        ],
    ),
    Row(
        to_top=True,
        cells=[
            Cell(column_id=full_name_column.id, value="Bob Lee"),
            Cell(column_id=num_books_column.id, value=2),
        ],
    ),
    Row(
        to_top=True,
        cells=[
            Cell(column_id=full_name_column.id, value="Charlie Brown"),
            Cell(column_id=num_books_column.id, value=1),
        ],
    ),
])

# getting an updated sheet
sheet = smartsheet.sheets.get('My New Sheet')
print("Sheet after adding rows:")
pprint(sheet.__dict__)

# getting a specific cell and updating it:
row_id_to_delete = None
rows_to_update = []
for row in sheet.rows:
    full_name = row.get_cell('Full Name').value
    num_books = row.get_cell('Number of read books').value
    print(f'{full_name} has read {num_books} books')
    if full_name.startswith('Charlie'):
        num_books_cell = row.get_cell('Number of read books')
        num_books_cell.value += 1
        rows_to_update.append(row)
    elif full_name.startswith('Bob'):
        row_id_to_delete = row.id  # used later

# update rows
sheet.update_rows(rows_to_update)
# or a single row
# sheet.update_rows(rows_to_update[0])

# getting an updated sheet
sheet = smartsheet.sheets.get('My New Sheet')
print("Sheet after updating rows:")
pprint(sheet.__dict__)

# deleting row by id
sheet.delete_row(row_id_to_delete)

# getting an updated sheet
sheet = smartsheet.sheets.get('My New Sheet')
print("Sheet after deleting rows:")
pprint(sheet.__dict__)

# deleting Sheet
# sheet = smartsheet.sheets.delete('My New Sheet')
sheets = smartsheet.sheets.list()
pprint(sheets)
