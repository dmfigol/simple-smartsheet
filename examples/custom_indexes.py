from simple_smartsheet import Smartsheet
from pprint import pprint
from decouple import config

TOKEN = config("SMARTSHEET_API_TOKEN")
smartsheet = Smartsheet(TOKEN)

INDEX_KEYS = [
    {"columns": ("Company Name",), "unique": False},
    {"columns": ("Company Name", "Full Name"), "unique": True},
    {"columns": ("Email Address",), "unique": True},
]
sheet = smartsheet.sheets.get("Index Test Sheet", index_keys=INDEX_KEYS)

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

pprint(sheet.get_row(filter={"Email Address": "charlie.brown@globex.com"}).as_dict())
# >
# {'Company Name': 'Globex',
#  'Email Address': 'charlie.brown@globex.com',
#  'Full Name': 'Charlie Brown'}

pprint(
    sheet.get_row(filter={"Full Name": "Alice Smith", "Company Name": "ACME"}).as_dict()
)
# >
# {'Company Name': 'ACME',
#  'Email Address': 'alice.smith@acme.com',
#  'Full Name': 'Alice Smith'}

pprint([row.as_dict() for row in sheet.get_rows(filter={"Company Name": "ACME"})])
# >
# [{'Company Name': 'ACME',
#   'Email Address': 'alice.smith@acme.com',
#   'Full Name': 'Alice Smith'},
#  {'Company Name': 'ACME',
#   'Email Address': 'bob.lee@acme.com',
#   'Full Name': 'Bob Lee'}]
