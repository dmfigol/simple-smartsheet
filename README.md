## Simple Smartsheet
Python library to interact with Smartsheet API easily

### Installation
Requires Python 3.6+  
`pip install simple-smartsheet`

### Why not smartsheet-python-sdk
`smartsheet-python-sdk` has very wide object coverage and maps to Smartsheet API very nicely, but it does not have some convenience features (for example, easy access to cells by column titles).  
`simple-smartsheet` library is focused on the user experience in expense of feature coverage. 
As of now, you can only interact with Sheets and Reports and their children objects (rows, columns, cells).  
Additionally, `simple-smartsheet` supports asyncio and provides both sync and async API at the same time.

### Usage
```python
import os
from datetime import date
from pprint import pprint

from simple_smartsheet import Smartsheet
from simple_smartsheet.models import Sheet, Column, Row, Cell, ColumnType

TOKEN = os.getenv("SMARTSHEET_API_TOKEN")
SHEET_NAME = "[TEST] My New Sheet"
smartsheet = Smartsheet(TOKEN)

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
```

### API reference
While a separate docs page is work in progress, available public API is described here
#### Class `simple_smartsheet.Smartsheet`
This class a main entry point for the library  
Methods:
  * `def __init__(token: str)`: constructor for the class
  
Attributes:
  * `token`: Smartsheet API token, obtained in Personal Settings -> API access
  * `sheets`: `simple_smartsheet.models.sheet.SheetCRUD` object which provides methods to interact with sheets
  * `reports`: `simple_smartsheet.models.report.ReportCRUD` object which provides methods to interact with reports
  
#### Class `simple_smartsheet.models.sheet.SheetCRUD`
Methods:
  * `def get(name: Optional[str], id: Optional[int]) -> Sheet`: fetches Sheet by name or ID.
  * `def list() -> List[Sheet]`: fetches a list of all sheets (summary only)
  * `def create(obj: Sheet) -> Result`: adds a new sheet
  * `def update(obj: Sheet) -> Result`: updates a sheet
  * `def delete(name: Optional[str], id: Optional[int]) -> Result`: deletes a sheet by name or ID
  * `def add_rows(sheet_id: int, rows: Sequence[Row]) -> Result`: adds rows to the sheet
  * `def add_row(sheet_id: int, row: Row) -> Result`: add a single row to the sheet
  * `def update_rows(sheet_id: int, rows: Sequence[Row]) -> Result`: updates several rows in the sheet
  * `def update_row(sheet_id: int, row: Row) -> Result`: updates a single row
  * `def delete_rows(sheet_id: int, row_ids: Sequence[int]) -> Result`: deletes several rows with provided ids
  * `def delete_row(sheet_id: int, row_id: int) -> Result`: deletes a single row with a provided id
  * `def sort_rows(sheet: Sheet, order: List[Dict[str, Any]]) -> Sheet`: sorts sheet rows with the specified order, e.g.:   
```
sheet.sort_rows([
    {"column_title": "Birth date", "descending": True},
    {"column_title": "Full Name"}
])
```

#### Class `simple_smartsheet.models.sheet.AsyncSheetCRUD`
The methods listed below are asynchronous version of methods in `SheetCRUD`, listed for completeness:
  * `async def get(name: Optional[str], id: Optional[int]) -> Sheet`
  * `async def list() -> List[Sheet]`
  * `async def create(obj: Sheet) -> Result`
  * `async def update(obj: Sheet) -> Result`
  * `async def delete(name: Optional[str], id: Optional[int]) -> Result`
  * `async def add_rows(sheet_id: int, rows: Sequence[Row]) -> Result`
  * `async def add_row(sheet_id: int, row: Row) -> Result`
  * `async def update_rows(sheet_id: int, rows: Sequence[Row]) -> Result`
  * `async def update_row(sheet_id: int, row: Row) -> Result`
  * `async def delete_rows(sheet_id: int, row_ids: Sequence[int]) -> Result`
  * `async def delete_row(sheet_id: int, row_id: int) -> Result`
  * `async def sort_rows(sheet: Sheet, order: List[Dict[str, Any]]) -> Sheet`

#### Class `simple_smartsheet.models.Sheet`
Attributes (converted from camelCase to snake_case):
  * <http://smartsheet-platform.github.io/api-docs/#sheets>
  
Methods:
  * `def get_row(row_num: Optional[int], row_id: Optional[int], filter: Optional[Dict[str, Any]]) -> Optional[Row]`: returns a Row object by row number, ID or by filter, if a unique index was built (see section "Custom Indexes")
  * `def get_rows(index_query: Dict[str, Any]) -> List[Row]`: returns list of Row objects by filter, if an index was built (see section "Custom Indexes")
  * `def get_column(column_title: Optional[str], column_id: Optional[int]) -> Column`: returns a Column object by column title or id
  * `def build_index(indexes: List[IndexKeysDict]) -> None`: builds one or more indexes for quick row lookup using `get_row` or `get_rows`, e.g.:  
```
sheet.build_index([
    {"columns": ("Company Name",), "unique": False},
    {"columns": ("Company Name", "Full Name"), "unique": True}
])
```  
  * `def make_cell(column_title: str, field_value: Union[float, str, datetime, None]) -> Cell`: creates a Cell object with provided column title and an associated value
  * `def make_cells(fields: Dict[str, Union[float, str, datetime, None]]) -> List[Cell]`: creates a list of Cell objects from an input dictionary where column title is key associated with the field value
  * `def as_list() -> List[Dict[str, Any]]`: returns a list of dictionaries where column title is key associated with the field value
  
#### Class `simple_smartsheet.models.row.Row`
Attributes (converted from camelCase to snake_case):
  * <http://smartsheet-platform.github.io/api-docs/#rows>
  * `rowNumber` is mapped to `num`
  
Methods:
  * `def get_cell(column_title: Optional[str], column_id: Optional[int]) -> Cell` - returns a Cell object by column title (case-sensitive) or column id
  * `def as_dict() -> Dict[str, Any]` - returns a dictionary of column title to cell value mappings

#### Class `simple_smartsheet.models.column.Column`
Attributes (converted from camelCase to snake_case):
  * <http://smartsheet-platform.github.io/api-docs/#columns>

#### Class `simple_smartsheet.models.cell.Cell`
Attributes (converted from camelCase to snake_case):
  * <http://smartsheet-platform.github.io/api-docs/#cells>

#### Class `simple_smartsheet.models.extra.Result`:
Attributes (converted from camelCase to snake_case):
  * <https://smartsheet-platform.github.io/api-docs/#result-object>
  * `result` attribute is renamed to `obj` to avoid confusion of calling `result.result`. `result` attribute is still available via property

#### Class `simple_smartsheet.models.Report`
Attributes (converted from camelCase to snake_case):
  * [http://smartsheet-platform.github.io/api-docs/#reports](http://smartsheet-platform.github.io/api-docs/#reports)
  
Implements the following Sheet methods:
  * `def get_row(row_num: Optional[int], row_id: Optional[int], filter: Optional[Dict[str, Any]]) -> ReportRow`: returns a ReportRow object by row number, ID or by filter, if a unique index was built (see section "Custom Indexes")
  * `def get_rows(index_query: Dict[str, Any]) -> List[ReportRow]`: returns list of ReportRow objects by filter, if an index was built (see section "Custom Indexes")
  * `def get_column(column_title: Optional[str], column_id: Optional[int]) -> ReportColumn`: returns a ReportColumn object by column title or id
  * `def build_index(indexes: List[IndexKeysDict]) -> None`: builds one or more indexes for quick row lookup using `get_row` or `get_rows`, e.g.:  
```
sheet.build_index([
    {"columns": ("Company Name",), "unique": False},
    {"columns": ("Company Name", "Full Name"), "unique": True}
])
```  
  * `def as_list() -> List[Dict[str, Any]]`: returns a list of dictionaries where column title is key associated with the field value
  
### Custom Indexes
It is possible to build indexes to enable quick rows lookups for sheets and reports. For this, after retrieving the sheet, call `sheet.build_index` function. It takes only one argument: a list of dictionaries, where every dictionary has two keys `columns` and `unique`. `columns` should contain a tuple with column titles (case sensitive). `unique` controls if the index always points to a single row (value `True`, lookups are done using `get_row` method) or multiple rows (value `False`, lookups are done using `get_rows` method).

Below you can find a code snippet (see the full example in `examples/custom_indexes.py`):
```python
INDEXES = [
    {"columns": ("Company",), "unique": False},
    {"columns": ("Company", "Full Name"), "unique": True},
    {"columns": ("Email address",), "unique": True},
]
sheet = smartsheet.sheets.get("[TEST] Index Sheet")
sheet.build_index(INDEXES)

print("\nRow where email address is 'charlie.brown@globex.com':")
print(sheet.get_row(filter={"Email Address": "charlie.brown@globex.com"}).as_dict())
# >
# {'Company Name': 'Globex',
#  'Email Address': 'charlie.brown@globex.com',
#  'Full Name': 'Charlie Brown'}

print("\nRows where the company name is 'ACME':")
print([row.as_dict() for row in sheet.get_rows(filter={"Company Name": "ACME"})])
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

### Pandas
If pandas is installed (either separately or as extras `pip install simple-smartsheet[pandas]`), sheets and rows can be exported as `pandas.DataFrame` or `pandas.Series` respectively. Besides column titles and respective values from the sheet, they will also include row IDs and row numbers
```
sheet = smartsheets.sheets.get('my-sheet')
df = sheet.as_dataframe()
series = sheet.rows[0].as_series()
```  
