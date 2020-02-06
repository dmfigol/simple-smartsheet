## Changelog
#### 0.5.0 (2020-02-06)
* Export sheets and rows as pandas dataframe and series respectively. #22  
  Install the package with pandas as extras: `pip install simple-smartsheet[pandas]`
* Add multi picklist support #28
* Do not crash when deleting many rows #25
* All crud methods directly on the `Sheet` object were removed, use `SheetCrud` methods instead, e.g. `smartsheet.sheets.add_rows`
#### 0.4.2 (2019-08-16)
* Add a more specific constraint to marshmallow dependency (Fix #18)
#### 0.4.1 (2019-08-16)
* Fetch more than 100 rows in a report (Fix #19)
#### 0.4.0 (2019-08-08)
* Add exception `SmartsheetObjectNotFound`
* Do not crash when an unknown field is encountered from API request
* Add new summary attributes to sheet and report schema #17 introduced by this feature <https://help.smartsheet.com/learning-track/smartsheet-intermediate/sheet-summary>
* Fix several bugs in some asyncio coroutines which were not awaited
* Add a number of integration tests against Smartsheet Developer sandbox
* [Deprecated] SheetCrud methods `add_row`, `add_rows`, `update_row`, `update_rows`, `delete_row`, `delete_rows` as well as their async counterparts now have `sheet_id: int` as a first argument instead of `sheet: Sheet` object. Deprecation warning is raised if you pass `Sheet` object as the first argument. `sort_rows` still uses `sheet` object as the first argument. 
* [Backwards incompatible] [Result object](https://smartsheet-platform.github.io/api-docs/#result-object) now converts the received object data into an object itself. It is accessible via `result.obj` or property `result.result` which points to the same attribute. This is important in some cases, e.g. new sheet creation: `result = smartsheet.sheets.create(new_sheet_skeleton)`. `result.obj` will contain a new `Sheet`, while `result.obj.id` will have an ID of a new sheet.
#### 0.3.0 (2019-06-26)
* Add asyncio support, check readme and `examples/async.py` for more details
* \[Deprecated\] All methods on Sheet object, which do API call, like `add_rows`, `update_rows`, `delete_rows`, `sort_rows`, they are now available under `smartsheet.sheets` and the first argument is sheet object
#### 0.2.0 (2019-04-18)
* Add support for Report objects
* \[Backwards incompatible\] Change the way indexes are handled, `build_index` method should be used on Sheet or Report objects
* Unchecked checkboxes return False instead of None (#12)
#### 0.1.11 (2019-04-02)
* Add exceptions SmartsheetHTTPClientError and SmartsheetHTTPServerError
#### 0.1.10 (2019-01-09)
* Change models.extra.AutoNumberFormat to support absent arguments [#7](https://github.com/dmfigol/simple-smartsheet/issues/7)
* Handle invalid values in dates and datetimes columns [#9](https://github.com/dmfigol/simple-smartsheet/issues/9)
#### 0.1.9 (2018-12-19)
* Add workspace to SheetSchema [#6](https://github.com/dmfigol/simple-smartsheet/issues/6)
* Handle missing "name" in contact options [#5](https://github.com/dmfigol/simple-smartsheet/issues/5)
#### 0.1.8 (2018-12-08)
* Fix contactOptions in ColumnSchema [#4](https://github.com/dmfigol/simple-smartsheet/issues/4)
#### 0.1.7 (2018-11-16)
* Change default sorting order to ascending [#3](https://github.com/dmfigol/simple-smartsheet/issues/3)
#### 0.1.6 (2018-11-16)
* Add `sort_rows` method for Sheet object
#### 0.1.5 (2018-11-15)
* Add support for date fields
#### 0.1.4 (2018-11-15)
* Add `make_cell` and `make_cells` methods for Sheet object
* Add `as_list` method for Sheet object
#### 0.1.3 (2018-11-12)
* Add marshmallow Schema to handle column options and tags #1
#### 0.1.2 (2018-11-09)
* Add `as_dict` method for Row object
* Add custom index support and querying based on it
#### 0.1.1 (2018-11-07)
* Change metadata for the package on PyPi
#### 0.1.0 (2018-11-07)
* First release
