import json
import os
import shutil
from datetime import date
from pathlib import Path

import pytest
from ruamel.yaml import YAML
from typing import List, Dict, Any
from vcr import VCR
from vcr.persisters.filesystem import FilesystemPersister

from simple_smartsheet import Smartsheet, AsyncSmartsheet
from simple_smartsheet.models import Column, Sheet, Row, ColumnType

SMARTSHEET_TOKEN = os.getenv("SMARTSHEET_API_TOKEN", "")
yaml = YAML(typ="safe")
yaml.default_flow_style = False


class MyPersister(FilesystemPersister):
    @classmethod
    def load_cassette(cls, cassette_path, serializer):
        path = Path(cassette_path)
        if path.is_file():
            path.unlink()
        raise ValueError("Cassette was deleted")


def pytest_addoption(parser):
    """Add custom command line options"""
    parser.addoption(
        "--delete-cassettes", action="store_true", help="Delete all cassettes",
    )
    parser.addoption(
        "--disable-vcr", action="store_true", help="Disable VCR",
    )


@pytest.fixture(scope="session")
def custom_cassette_dir(pytestconfig):
    return Path(pytestconfig.rootdir) / "tests/sandbox/crud/cassettes"


@pytest.fixture(scope="session")
def custom_vcr(pytestconfig, custom_cassette_dir):
    """Session VCR fixture for fixture setup/teardown"""
    record_mode = pytestconfig.getoption("--record-mode")
    config = {
        "cassette_library_dir": str(custom_cassette_dir),
        "decode_compressed_response": True,
        "filter_headers": [("authorization", "[REDACTED]")],
        "record_mode": record_mode,
    }
    if pytestconfig.getoption("--disable-vcr"):
        config["record_mode"] = "new_episodes"
        config["before_record_response"] = lambda *args, **kwargs: None

    vcr = VCR(**config)
    # if record_mode == "all":
    #     vcr.register_persister(MyPersister)
    return vcr


@pytest.fixture(scope="module")
def vcr_config(pytestconfig):
    """Overwriting  pytest-recording 'vcr-config' fixture"""
    config = {
        "decode_compressed_response": True,
        "filter_headers": [("authorization", "[REDACTED]")],
    }
    if pytestconfig.getoption("--disable-vcr"):
        config["record_mode"] = "new_episodes"
        config["before_record_response"] = lambda *args, **kwargs: None
    return config


# @pytest.fixture
# def vcr(vcr, pytestconfig):
#     """Overwriting pytest-recording 'vcr' fixture"""
#     record_mode = pytestconfig.getoption("--record-mode")
#     if record_mode == "all":
#         vcr.register_persister(MyPersister)
#     return vcr


def columns_gen() -> List[Column]:
    return [
        Column(primary=True, title="Full Name", type=ColumnType.TEXT_NUMBER),
        Column(title="Email address", type=ColumnType.TEXT_NUMBER),
        Column(title="Company", type=ColumnType.TEXT_NUMBER),
        Column(title="Number of children", type=ColumnType.TEXT_NUMBER),
        Column(
            title="Maintains",
            type=ColumnType.MULTI_PICKLIST,
            options=["simple-smartsheet", "nornir", "napalm", "netmiko", "pydantic"],
        ),
        Column(title="Birth date", type=ColumnType.DATE),
        Column(title="Married", type=ColumnType.CHECKBOX),
    ]


# noinspection PyArgumentList
@pytest.fixture
def placeholder_sheet() -> Sheet:
    return Sheet(name="[TEST] Placeholder", columns=columns_gen())


def rows_data_gen() -> List[Dict[str, Any]]:
    return [
        {
            "Full Name": "Bob Lee",
            "Email address": "bob.lee@acme.com",
            "Company": "ACME",
            "Number of children": 2,
            "Married": True,
            "Maintains": ["simple-smartsheet", "nornir"],
        },
        {
            "Full Name": "Alice Smith",
            "Email address": "alice.smith@globex.com",
            "Company": "Globex",
            "Maintains": ["napalm", "nornir"],
        },
        {
            "Full Name": "Charlie Brown",
            "Email address": "charlie.brown@acme.com",
            "Company": "ACME",
            "Number of children": 1,
            "Birth date": date(1990, 1, 1),
            "Married": False,
            "Maintains": ["napalm", "netmiko", "nornir"],
        },
    ]


def additional_row_data_gen() -> Dict[str, Any]:
    return {
        "Full Name": "David Ward",
        "Email address": "david.ward@globex.com",
        "Company": "Globex",
        "Number of children": 3,
        "Birth date": date(1980, 1, 1),
        "Married": True,
        "Maintains": ["pydantic"],
    }


@pytest.fixture
def rows_data() -> List[Dict[str, Any]]:
    return rows_data_gen()


@pytest.fixture
def additional_row_data() -> Dict[str, Any]:
    return additional_row_data_gen()


@pytest.fixture
def additional_rows_data() -> List[Dict[str, Any]]:
    return [
        {
            "Full Name": "David Ward",
            "Email address": "david.ward@globex.com",
            "Company": "Globex",
            "Number of children": 3,
            "Birth date": date(1980, 1, 1),
            "Married": True,
            "Maintains": ["pydantic"],
        },
        {
            "Full Name": "Elizabeth Warner",
            "Email address": "elizabeth.warner@acme.com",
            "Company": "ACME",
            "Number of children": 2,
            "Birth date": date(1985, 1, 1),
            "Married": True,
        },
    ]


@pytest.fixture
def mocked_sheet(pytestconfig) -> Sheet:
    path = Path(pytestconfig.rootdir) / "tests/sandbox/data/mocked_sheet.json"
    with open(path) as f:
        data = json.load(f)
        sheet = Sheet.load(data)
    return sheet


def fix_cassette(path: Path):
    # noinspection PyTypeChecker
    with open(path, "r+") as f:
        data = yaml.load(f)
        changed = False
        for i, req_resp in enumerate(data["interactions"]):
            request = req_resp["request"]
            url = request["uri"]
            method = request["method"]
            response = req_resp["response"]

            tests_sheets_data = []
            if method == "GET" and url in {
                "https://api.smartsheet.com/2.0/sheets?includeAll=true",
                "https://api.smartsheet.com/2.0/reports?includeAll=true",
            }:
                body = json.loads(response["body"]["string"])
                num_sheets = body["totalCount"]
                sheets = body["data"]
                for sheet_data in sheets:
                    sheet_name = sheet_data["name"]
                    if sheet_name.startswith("[TEST]"):
                        tests_sheets_data.append(sheet_data)

                if len(tests_sheets_data) != num_sheets:
                    body["totalCount"] = len(tests_sheets_data)
                    body["data"] = tests_sheets_data
                    changed = True
                    f.seek(0)
                    response["body"]["string"] = json.dumps(body)
                    f.truncate()

        if changed:
            f.seek(0)
            yaml.dump(data, f)


def remove_all_rw_objects(custom_vcr):
    with custom_vcr.use_cassette("remove_all_rw_objects.yaml"):
        with Smartsheet(SMARTSHEET_TOKEN) as smartsheet:
            for sheet in smartsheet.sheets.list():
                if sheet.name.startswith("[TEST]") and not any(
                    pattern in sheet.name for pattern in ("[TEST] Report",)
                ):
                    smartsheet.sheets.delete(id=sheet.id)


def create_sheets_for_reports(vcr):
    with vcr.use_cassette("setup_sheets_for_reports.yaml"):
        with Smartsheet(SMARTSHEET_TOKEN) as smartsheet:
            report_sheet1 = Sheet(name="[TEST] Report Sheet 1", columns=columns_gen())
            result = smartsheet.sheets.create(report_sheet1)
            report_sheet1 = result.obj
            rows = [
                Row(to_top=True, cells=report_sheet1.make_cells(row_data))
                for row_data in rows_data_gen()
            ]
            smartsheet.sheets.add_rows(report_sheet1.id, rows)

            report_sheet2 = Sheet(name="[TEST] Report Sheet 2", columns=columns_gen())
            result = smartsheet.sheets.create(report_sheet2)
            report_sheet2 = result.obj
            row = Row(
                to_top=True, cells=report_sheet2.make_cells(additional_row_data_gen())
            )
            smartsheet.sheets.add_row(report_sheet2.id, row)


def create_session_objects(vcr):
    with vcr.use_cassette("create_session_objects.yaml"):
        with Smartsheet(SMARTSHEET_TOKEN) as smartsheet:
            read_only_sheet = Sheet(
                name="[TEST] Read-only Sheet", columns=columns_gen()
            )
            result = smartsheet.sheets.create(read_only_sheet)
            read_only_sheet = result.obj
            rows = [
                Row(to_top=True, cells=read_only_sheet.make_cells(row_data))
                for row_data in rows_data_gen()
            ]
            smartsheet.sheets.add_rows(read_only_sheet.id, rows)


@pytest.fixture(scope="session", autouse=True)
def setup_teardown(request, custom_vcr, custom_cassette_dir):
    os.environ["SIMPLE_SMARTSHEET_STRICT_VALIDATION"] = "1"

    delete_cassettes = request.config.getoption("--delete-cassettes")
    if delete_cassettes:
        shutil.rmtree(custom_cassette_dir)
        custom_cassette_dir.mkdir(parents=True, exist_ok=True)

    remove_all_rw_objects(custom_vcr)
    create_session_objects(custom_vcr)
    yield


@pytest.fixture
def smartsheet():
    with Smartsheet(SMARTSHEET_TOKEN) as smartsheet:
        yield smartsheet


@pytest.fixture
async def async_smartsheet():
    async with AsyncSmartsheet(SMARTSHEET_TOKEN) as smartsheet:
        yield smartsheet
