import os

from simple_smartsheet import Smartsheet
from simple_smartsheet.models import Sheet, Row, Column, ColumnType

from pprint import pprint

TOKEN = os.getenv("SMARTSHEET_API_TOKEN")

INDEXES = [
    {"columns": ("Company",), "unique": False},
    {"columns": ("Company", "Full Name"), "unique": True},
    {"columns": ("Email address",), "unique": True},
]
INDEX_SHEET_NAME = "[TEST] Index Sheet"
INDEX_SHEET = Sheet(
    name=INDEX_SHEET_NAME,
    columns=[
        Column(primary=True, title="Full Name", type=ColumnType.TEXT_NUMBER),
        Column(title="Email address", type=ColumnType.TEXT_NUMBER),
        Column(title="Company", type=ColumnType.TEXT_NUMBER),
    ],
)

ROWS_DATA = [
    {"Full Name": "Bob Lee", "Email address": "bob.lee@acme.com", "Company": "ACME"},
    {
        "Full Name": "Alice Smith",
        "Email address": "alice.smith@globex.com",
        "Company": "Globex",
    },
    {
        "Full Name": "Charlie Brown",
        "Email address": "charlie.brown@acme.com",
        "Company": "ACME",
    },
]


def create_index_sheet_if_not_exists(
    smartsheet: Smartsheet, delete_existing: bool = False
) -> None:
    for sheet in smartsheet.sheets.list():
        if sheet.name == INDEX_SHEET.name:
            if delete_existing:
                smartsheet.sheets.delete(id=sheet.id)
            else:
                return

    result = smartsheet.sheets.create(INDEX_SHEET)
    rows = [
        Row(to_bottom=True, cells=result.obj.make_cells(row_data))
        for row_data in ROWS_DATA
    ]
    smartsheet.sheets.add_rows(result.obj.id, rows)


def main() -> None:
    with Smartsheet(TOKEN) as smartsheet:
        create_index_sheet_if_not_exists(smartsheet, delete_existing=False)
        sheet = smartsheet.sheets.get(INDEX_SHEET_NAME)
        sheet.build_index(INDEXES)

        pprint(sheet.indexes)
        # >
        # {('Company',): {'index': {('ACME',): [Row(id=8113413857011588, num=1),
        #                                       Row(id=5298664089905028, num=3)],
        #                           ('Globex',): [Row(id=795064462534532, num=2)]},
        #                 'unique': False},
        #  ('Company', 'Full Name'): {
        #      'index': {('ACME', 'Bob Lee'): Row(id=8113413857011588, num=1),
        #                ('ACME', 'Charlie Brown'): Row(id=5298664089905028, num=3),
        #                ('Globex', 'Alice Smith'): Row(id=795064462534532, num=2)},
        #      'unique': True},
        #  ('Email address',): {
        #      'index': {('alice.smith@globex.com',): Row(id=795064462534532, num=2),
        #                ('bob.lee@acme.com',): Row(id=8113413857011588, num=1),
        #                ('charlie.brown@acme.com',): Row(id=5298664089905028, num=3)},
        #      'unique': True}}

        pprint(sheet.as_list())
        # >
        # [{'Company': 'ACME',
        #   'Email address': 'bob.lee@acme.com',
        #   'Full Name': 'Bob Lee'},
        #  {'Company': 'Globex',
        #   'Email address': 'alice.smith@globex.com',
        #   'Full Name': 'Alice Smith'},
        #  {'Company': 'ACME',
        #   'Email address': 'charlie.brown@acme.com',
        #   'Full Name': 'Charlie Brown'}]

        print("\nRow where email address is 'charlie.brown@acme.com':")
        pprint(
            sheet.get_row(filter={"Email address": "charlie.brown@acme.com"}).as_dict()
        )
        # >
        # {'Company': 'ACME',
        #  'Email address': 'charlie.brown@acme.com',
        #  'Full Name': 'Charlie Brown'}

        print("\nRow where full name is 'Bob Lee' and the company name is 'ACME':")
        pprint(
            sheet.get_row(filter={"Full Name": "Bob Lee", "Company": "ACME"}).as_dict()
        )
        # >
        # {'Company': 'ACME', 'Email address': 'bob.lee@acme.com', 'Full Name': 'Bob Lee'}

        print("\nRows where the company name is 'ACME':")
        pprint([row.as_dict() for row in sheet.get_rows(filter={"Company": "ACME"})])
        # >
        # [{'Company': 'ACME',
        #   'Email address': 'bob.lee@acme.com',
        #   'Full Name': 'Bob Lee'},
        #  {'Company': 'ACME',
        #   'Email address': 'charlie.brown@acme.com',
        #   'Full Name': 'Charlie Brown'}]


if __name__ == "__main__":
    if TOKEN:
        main()
