import asyncio
import os

import pytest

from simple_smartsheet import AsyncSmartsheet


SHEET_IDS = [
    int(id_) for id_ in os.getenv("SMARTSHEET_PROD_SHEET_IDS", "").split(",") if id_
]
REPORT_IDS = [
    int(id_) for id_ in os.getenv("SMARTSHEET_PROD_REPORT_IDS", "").split(",") if id_
]

TOKEN = os.getenv("SMARTSHEET_API_TOKEN_PROD")


@pytest.fixture(scope="module", autouse=True)
def skip_fixture():
    if not os.getenv("SMARTSHEET_API_TOKEN_PROD"):
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
