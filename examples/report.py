import os
from pprint import pprint

from simple_smartsheet import Smartsheet

TOKEN = os.environ["SMARTSHEET_API_TOKEN"]


def main() -> None:
    with Smartsheet(TOKEN) as smartsheet:
        # retrieve a list of reports (limited set of attributes)
        reports = smartsheet.reports.list()
        pprint(reports)

        # get the report by the name and build an index
        report = smartsheet.reports.get("[TEST] Read-only Report")
        report.build_index([{"columns": ("Full Name",), "unique": True}])

        # print a list of dictionaries containing column titles and values for each row
        pprint(report.as_list())
        # print built indexes
        pprint(report.indexes)

        # use the index to retrieve a row
        print("\nRow where the full name is 'David Ward':")
        pprint(report.get_row(filter={"Full Name": "David Ward"}).as_dict())


if __name__ == "__main__":
    main()
