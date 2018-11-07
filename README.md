## Simple Smartsheet
Python library to interact with Smartsheet API easily

### Installation
Requires Python 3.6+  
`pip install simple-smartsheet`

### Why not smartsheet-python-sdk
`smartsheet-python-sdk` has very wide object coverage and maps to Smartsheet API very nicely, but it does not have any additional features (for example, easy access to cells by column titles).  
`simple-smartsheet` library is focused on user experience first in expense of feature coverage. 
As of now, you can only interact with Sheets and nested objects (rows, columns, cells).

### Code Example
```python
from simple_smartsheet import Smartsheet
from simple_smartsheet.models import Sheet, Column, Row, Cell
from pprint import pprint

TOKEN = 'my-smartsheet-token'
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
sheet = smartsheet.sheets.delete('My New Sheet')
sheets = smartsheet.sheets.list()
pprint(sheets)
```

### Docs
While a separate docs page is work in progress, available public API is described here
#### Class `simple_smartsheet.Smartsheet`
This class a main entry point for the library  
Methods:
  * `def __init__(token: str)`: constructor for the class
  
Attributes:
  * `token`: Smartsheet API token, obtained in Personal Settings -> API access
  * `session`: requests.Session object which stores headers based on the token
  * `sheets`: `simple_smartsheet.models.sheet.SheetsCRUD` object which provides methods to interact with Sheets
  
#### Class `simple_smartsheet.models.sheet.SheetsCRUD`
Methods:
  * `def get(name: Optional[str], id: Optional[int])`: fetches Sheet by name or ID
  * `def list()`: fetches a list of all sheets (summary only)
  * `def create(obj: Sheet)`: adds a new sheet
  * `def update(obj: Sheet)`: updates a sheet
  * `def delete(name: Optional[str], id: Optional[int])`: deletes a sheet by name or ID

#### Class `simple_smartsheet.models.Sheet`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#sheets](http://smartsheet-platform.github.io/api-docs/#sheets)
  
Methods:
  * `def update_index()`: rebuilds mapping tables for rows and columns for quick lookup
  * `def get_row(row_num: Optional[int], row_id: Optional[int])`: returns a Row object by row number or ID
  * `def get_column(column_title: Optional[str], column_id: Optional[int])`: returns a Column object by column title or id
  * `def add_rows(rows: Sequence[Row])`: adds rows to the sheet
  * `def add_row(row: Row)`: add a single row to the sheet
  * `def update_rows(rows: Sequence[Row])`: updates several rows in the sheet
  * `def update_row(row: Row)`: updates a single row
  * `def delete_rows(row_ids: Sequence[int])`: delete several rows with provided ids
  * `def delete_row(row_id: int)`: delete a single row with a provided id
  
#### Class `simple_smartsheet.models.Row`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#rows](http://smartsheet-platform.github.io/api-docs/#rows)
  * `rowNumber` is mapped to `num`
  
Methods:
  * `def get_cell(column_title: Optional[str], column_id: Optional[int])` - returns a Cell object by column title (case-sensitive) or column id

#### Class `simple_smartsheet.models.Column`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#columns](http://smartsheet-platform.github.io/api-docs/#columns)

#### Class `simple_smartsheet.models.Cell`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#cells](http://smartsheet-platform.github.io/api-docs/#cells)