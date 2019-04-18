## Changelog
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