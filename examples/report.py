import os
from pprint import pprint

from simple_smartsheet import Smartsheet

TOKEN = os.environ["SMARTSHEET_API_TOKEN"]
with Smartsheet(TOKEN) as smartsheet:
    # getting a simplified view of available reports
    reports = smartsheet.reports.list()
    pprint(reports)

    # getting the report by the name and build an index
    report = smartsheet.reports.get("My Test Report")
    report.build_index([{"columns": ("Full Name",), "unique": True}])

    # printing the sheet object attributes
    pprint(report.__dict__)
    # or printing the sheet object as a dictionary which will be used in REST API
    pprint(report.dump())
    pprint(report.as_list())
    # print indexes
    pprint(report.indexes)

    # using index
    print("\nRow where the full name is 'Diane':")
    pprint(report.get_row(filter={"Full Name": "Diane"}).as_dict())
