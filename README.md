## Simple Smartsheet
Python library to interact with Smartsheet API easily

### Installation
Requires Python 3.6+  
`pip install simple-smartsheet`

### Why not smartsheet-python-sdk
`smartsheet-python-sdk` has very wide object coverage and maps to Smartsheet API very nicely, but it does not have any additional features (for example, easy access to cells by column titles).  
`simple-smartsheet` library is focused on user experience first in expense of feature coverage. 
As of now, you can only interact with Sheets and Reports and their children objects (rows, columns, cells).  
Also `simple-smartsheet` support asyncio and provided both sync and async API (asyncio).

### Usage
```python
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
        Column(title="Library member", type="CHECKBOX"),
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
smartsheet.sheets.add_rows(sheet,
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
            cells=sheet.make_cells({"Full Name": "Bob Lee", "Number of read books": 2}),
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
sheet = smartsheet.sheets.sort_rows(sheet, [{"column_title": "Full Name", "descending": True}])

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
smartsheet.sheets.update_rows(sheet, rows_to_update)
# or a single row
# sheet.update_rows(rows_to_update[0])

# getting an updated sheet
sheet = smartsheet.sheets.get("My New Sheet")
print("\nSheet after updating rows:")
pprint(sheet.as_list())

# deleting row by id
sheet.delete_row(sheet, row_id_to_delete)

# getting an updated sheet
sheet = smartsheet.sheets.get("My New Sheet")
print("\nSheet after deleting rows:")
pprint(sheet.as_list())

# deleting Sheet
sheet = smartsheet.sheets.delete("My New Sheet")
sheets = smartsheet.sheets.list()
pprint(sheets)
```

### API reference
While a separate docs page is work in progress, available public API is described here
#### Class `simple_smartsheet.Smartsheet`
This class a main entry point for the library  
Methods:
  * `def __init__(token: str)`: constructor for the class
  
Attributes:
  * `token`: Smartsheet API token, obtained in Personal Settings -> API access
  * `session`: requests.Session object which stores headers based on the token
  * `sheets`: `simple_smartsheet.models.sheet.SheetCRUD` object which provides methods to interact with Sheets
  
#### Class `simple_smartsheet.models.sheet.SheetCRUD`
Methods:
  * `def get(name: Optional[str], id: Optional[int])`: fetches Sheet by name or ID.
  * `def list()`: fetches a list of all sheets (summary only)
  * `def create(obj: Sheet)`: adds a new sheet
  * `def update(obj: Sheet)`: updates a sheet
  * `def delete(name: Optional[str], id: Optional[int])`: deletes a sheet by name or ID
  * `def add_rows(sheet: Sheet, rows: Sequence[Row])`: adds rows to the sheet
  * `def add_row(sheet: Sheet, row: Row)`: add a single row to the sheet
  * `def update_rows(sheet: Sheet, rows: Sequence[Row])`: updates several rows in the sheet
  * `def update_row(sheet: Sheet, row: Row)`: updates a single row
  * `def delete_rows(sheet: Sheet, row_ids: Sequence[int])`: deletes several rows with provided ids
  * `def delete_row(sheet: Sheet, row_id: int)`: deletes a single row with a provided id
  * `def sort_rows(sheet, order: List[Dict[str, Any]])`: sorts sheet rows with the specified order, e.g.:   
```
sheet.sort_rows([
    {"column_title": "Birth date", "descending": True},
    {"column_title": "Full Name"}
])
```

#### Class `simple_smartsheet.models.sheet.SheetAsyncCRUD`
The methods listed below are asynchronous version of methods in `SheetCRUD`, listed for completeness:
  * `async def get(name: Optional[str], id: Optional[int])`
  * `async def list()`
  * `async def create(obj: Sheet)`
  * `async def update(obj: Sheet)`
  * `async def delete(name: Optional[str], id: Optional[int])`
  * `async def add_rows(sheet: Sheet, rows: Sequence[Row])`
  * `async def add_row(sheet: Sheet, row: Row)`
  * `async def update_rows(sheet: Sheet, rows: Sequence[Row])`
  * `async def update_row(sheet: Sheet, row: Row)`
  * `async def delete_rows(sheet: Sheet, row_ids: Sequence[int])`
  * `async def delete_row(sheet: Sheet, row_id: int)`
  * `async def sort_rows(sheet, order: List[Dict[str, Any]])`

#### Class `simple_smartsheet.models.Sheet`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#sheets](http://smartsheet-platform.github.io/api-docs/#sheets)
  
Methods:
  * `def get_row(row_num: Optional[int], row_id: Optional[int], filter: Optional[Dict[str, Any]])`: returns a Row object by row number, ID or by filter, if a unique index was built (see section "Custom Indexes")
  * `def get_rows(index_query: Dict[str, Any])`: returns list of Row objects by filter, if an index was built (see section "Custom Indexes")
  * `def get_column(column_title: Optional[str], column_id: Optional[int])`: returns a Column object by column title or id
  * `def build_index(indexes: List[IndexKeysDict])`: builds one or more indexes for quick row lookup using `get_row` or `get_rows`, e.g.:  
```
sheet.build_index([
    {"columns": ("Company Name",), "unique": False},
    {"columns": ("Company Name", "Full Name"), "unique": True}
])
```  
  * `def make_cell(column_title: str, field_value: Union[float, str, datetime, None])`: creates a Cell object with provided column title and an associated value
  * `def make_cells(fields: Dict[str, Union[float, str, datetime, None]])`: creates a list of Cell objects from an input dictionary where column title is key associated with the field value
  * `def as_list()`: returns a list of dictionaries where column title is key associated with the field value
  
#### Class `simple_smartsheet.models.row.Row`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#rows](http://smartsheet-platform.github.io/api-docs/#rows)
  * `rowNumber` is mapped to `num`
  
Methods:
  * `def get_cell(column_title: Optional[str], column_id: Optional[int])` - returns a Cell object by column title (case-sensitive) or column id
  * `def as_dict()` - returns a dictionary of column title to cell value mappings

#### Class `simple_smartsheet.models.column.Column`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#columns](http://smartsheet-platform.github.io/api-docs/#columns)

#### Class `simple_smartsheet.models.cell.Cell`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#cells](http://smartsheet-platform.github.io/api-docs/#cells)

#### Class `simple_smartsheet.models.Report`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#reports](http://smartsheet-platform.github.io/api-docs/#reports)
  
Implements the following Sheet methods:
  * `def get_row(row_num: Optional[int], row_id: Optional[int], filter: Optional[Dict[str, Any]])`: returns a Row object by row number, ID or by filter, if a unique index was built (see section "Custom Indexes")
  * `def get_rows(index_query: Dict[str, Any])`: returns list of Row objects by filter, if an index was built (see section "Custom Indexes")
  * `def get_column(column_title: Optional[str], column_id: Optional[int])`: returns a Column object by column title or id
  * `def build_index(indexes: List[IndexKeysDict])`: builds one or more indexes for quick row lookup using `get_row` or `get_rows`, e.g.:  
```
sheet.build_index([
    {"columns": ("Company Name",), "unique": False},
    {"columns": ("Company Name", "Full Name"), "unique": True}
])
```  
  * `def as_list()`: returns a list of dictionaries where column title is key associated with the field value
  
### Custom Indexes
It is possible to build indexes to enable quick rows lookups. For this, after retrieving the sheet, call `sheet.build_index` function. It takes only one argument: a list of dictionaries, where every dictionary has two keys `columns` and `unique`. `columns` should contain a tuple with column titles (case sensitive). `unique` controls if the index always points to a single row (value `True`, lookups are done using `get_row` method) or multiple rows (value `False`, lookups are done using `get_rows` method).

Below you can find a code example:
```python
import os

from simple_smartsheet import Smartsheet

from pprint import pprint

TOKEN = os.getenv("SMARTSHEET_API_TOKEN")
smartsheet = Smartsheet(TOKEN)

INDEXES = [
    {"columns": ("Company Name",), "unique": False},
    {"columns": ("Company Name", "Full Name"), "unique": True},
    {"columns": ("Email Address",), "unique": True},
]
sheet = smartsheet.sheets.get("Index Test Sheet")
sheet.build_index(INDEXES)

pprint(sheet.indexes)
# >
# defaultdict(<class 'dict'>,
#             {('Company Name',): {('ACME',): [Row(id=525791232583556, num=1),
#                                              Row(id=5029390859954052, num=2)],
#                                  ('Globex',): [Row(id=2777591046268804, num=3)]},
#              ('Company Name', 'Full Name'): {('ACME', 'Alice Smith'): Row(id=525791232583556, num=1),
#                                              ('ACME', 'Bob Lee'): Row(id=5029390859954052, num=2),
#                                              ('Globex', 'Charlie Brown'): Row(id=2777591046268804, num=3)},
#              ('Email Address',): {('alice.smith@acme.com',): Row(id=525791232583556, num=1),
#                                   ('bob.lee@acme.com',): Row(id=5029390859954052, num=2),
#                                   ('charlie.brown@globex.com',): Row(id=2777591046268804, num=3)}})

pprint(sheet.as_list())
# >
# [{'Company Name': 'ACME',
#   'Email Address': 'alice.smith@acme.com',
#   'Full Name': 'Alice Smith'},
#  {'Company Name': 'ACME',
#   'Email Address': 'bob.lee@acme.com',
#   'Full Name': 'Bob Lee'},
#  {'Company Name': 'Globex',
#   'Email Address': 'charlie.brown@globex.com',
#   'Full Name': 'Charlie Brown'}]

print("\nRow where email address is 'charlie.brown@globex.com':")
pprint(sheet.get_row(filter={"Email Address": "charlie.brown@globex.com"}).as_dict())
# >
# {'Company Name': 'Globex',
#  'Email Address': 'charlie.brown@globex.com',
#  'Full Name': 'Charlie Brown'}

print("\nRow where full name is 'Alice Smith' and the company name is 'ACME':")
pprint(
    sheet.get_row(filter={"Full Name": "Alice Smith", "Company Name": "ACME"}).as_dict()
)
# >
# {'Company Name': 'ACME',
#  'Email Address': 'alice.smith@acme.com',
#  'Full Name': 'Alice Smith'}

print("\nRows where the company name is 'ACME':")
pprint([row.as_dict() for row in sheet.get_rows(filter={"Company Name": "ACME"})])
# >
# [{'Company Name': 'ACME',
#   'Email Address': 'alice.smith@acme.com',
#   'Full Name': 'Alice Smith'},
#  {'Company Name': 'ACME',
#   'Email Address': 'bob.lee@acme.com',
#   'Full Name': 'Bob Lee'}]
``` 

### Asyncio
The library supports asyncio for all i/o methods, instead of calling:
```
smartsheet = Smartsheet(token)
sheet = smartsheets.sheets.get('my-sheet')
```  
you need to call asynchronous context manager with an async version of smartsheet class:
```
with AsyncSmartsheet(token) as smartsheet:
   sheet = await smartsheet.sheets.get('my-sheet')
```

A complete asyncio example with different operations on sheets and reports can be found in `examples/async.py`