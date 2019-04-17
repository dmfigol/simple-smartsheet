## How to contribute to the project
1) Submit issues and feature requests on GitHub.  
Please remember that I am a single maintainer of this open-source project, so set your expectations accordingly.
2) Submit PR. Below you can find some details on how to get started if you would like to contribute code.

### Dev tools
* Python 3.6+
* [poetry](https://github.com/sdispater/poetry) - Python project management tool. After git cloning the project, just do `poetry install`. To run any Python project specific commands like `python <script>.py`, `black`, `mypy` prepend them with `poetry run`
* [black](https://github.com/ambv/black) - Python code formatter
* flake8 - linting tool
* mypy - static type analysis tool. The codebase is 100% annotated according to PEP-484 and PEP-526 

### Project architecture
#### marshmallow, attrs, cattrs
The project heavily relies on the following libraries: attrs, cattrs, marshmallow. If you want to add a support of new objects, please make sure you dedicate some time understanding these libraries. Here is the brief explanation, how they are used in this project
* marshmallow - responsible for the data validation (Schema), as well as serialization/desealization. It is doing conversion of keys (mostly from camelCase to snake_case) as well as conversion of simple types, for example datetime timestamps received in JSON will be converted to Python datetime. Marshmallow is an intermediary between API and the rest of the library. Every Smartsheet object has an associated marshmallow schema which is inherited from `simple_smartsheet.models.base.Schema`
* attrs - this Python library reduces the boilerplate code when creating Python classes. Every Smartsheet object has an associated class created with `attrs` and inherits from `simple_smartsheet.models.base.SmartsheetObject`
* cattrs - this Python library does structuring and unstructing of the Python `attrs` object: it converts Python dictionaries received from marshmallow to actual Python objects. It works even for nested objects (for example, Sheet contains columns and rows and rows contain cells). It is used in `simple_smartsheet.models.base.Object` `load` class method

#### `simple_smartsheet.models.base` 
There are two types of objects: objects and core objects. Core objects are  top level objects, which are going to be exposed to the user via `smartsheet.<plural-name>.<operation>`, for example Sheet object and an example operation `smartsheet.sheets.get('sheet-name')`. There are other non-core objects, for example **Column** or **Row**. These objects are somehow bounded to core objects (like **Sheet**), but user can't interact with them from api object directly. Those should be operations defined on a core object. For example **Sheet** object has method **update_rows**.
Every object has:
 * marshmallow schema: inherited from `simple_smartsheet.models.base.Schema`. Core object inherit from `simple_smartsheet.models.base.CoreSchema`
 * attrs class: inherited from `simple_smartsheet.models.base.Object`. Core object inherits from `simple_smartsheet.models.base.CoreObject`
 * CRUD class (only for core objects), inherited from `simple_smartsheet.models.base.CRUD`. This class defines operations available for a core object. Here is the list of common operations, already implemented in `CRUD` class:
   * get - get an object by name or ID
   * list - get all summary of all objects
   * create - create a new object
   * update - update an object
   * delete - delete an object  
 