import asyncio
import os

import pytest

from simple_smartsheet import AsyncSmartsheet

SHEET_IDS = [
    1542164917315460,
    1542164917315460,
    5371296302294916,
    6417264837715844,
    3103471428757380,
]
REPORT_IDS = [3135027476227972, 4507550579222404]

TOKEN = os.getenv("SMARTSHEET_API_TOKEN_PROD")


@pytest.fixture(scope="module", autouse=True)
def skip_fixture(pytestconfig):
    prod = pytestconfig.getoption("--prod")
    if not prod:
        pytest.skip("Test against production environment")


@pytest.mark.asyncio
async def test_sheets():
    async with AsyncSmartsheet(TOKEN) as smartsheet:
        futures = [
            asyncio.ensure_future(smartsheet.sheets.get(id=sheet_id))
            for sheet_id in SHEET_IDS
        ]
        await asyncio.gather(*futures)


@pytest.mark.asyncio
async def test_reports():
    async with AsyncSmartsheet(TOKEN) as smartsheet:
        futures = [
            asyncio.ensure_future(smartsheet.reports.get(id=report_id))
            for report_id in REPORT_IDS
        ]
        await asyncio.gather(*futures)
        assert len(futures[1].result().rows) > 1000
