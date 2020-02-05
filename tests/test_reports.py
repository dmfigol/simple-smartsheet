from datetime import date
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from simple_smartsheet.models.report import Report
    from simple_smartsheet import Smartsheet, AsyncSmartsheet


class TestListReports:
    @pytest.mark.vcr("list_reports.yaml")
    def test_list_reports(self, smartsheet: "Smartsheet"):
        reports = smartsheet.reports.list()
        assert any(report.name == "[TEST] Read-only Report" for report in reports)
        assert len(reports) == 1

    @pytest.mark.asyncio
    @pytest.mark.vcr("list_reports_async.yaml")
    async def test_list_reports_async(self, async_smartsheet: "AsyncSmartsheet"):
        reports = await async_smartsheet.reports.list()
        assert any(report.name == "[TEST] Read-only Report" for report in reports)
        assert len(reports) == 1


class TestGetReport:
    INDEXES = [
        {"columns": ("Company",), "unique": False},
        {"columns": ("Company", "Full Name"), "unique": True},
        {"columns": ("Email address",), "unique": True},
    ]
    REPORT_NAME = "[TEST] Read-only Report"

    def check_indexes(self, report: "Report"):
        report.build_index(self.INDEXES)
        row = report.get_row(filter={"Email address": "david.ward@globex.com"})
        assert row.get_cell("Email address").value == "david.ward@globex.com"
        assert row.get_cell("Full Name").value == "David Ward"
        assert row.get_cell("Birth date").value == date(1980, 1, 1)
        assert row.get_cell("Married").value
        assert row.get_cell("Number of children").value == 3.0

        rows = report.get_rows(filter={"Company": "Globex"})
        assert len(rows) == 2
        for row in rows:
            assert row.get_cell("Company").value == "Globex"

    def check_report(self, report: "Report"):
        assert report.name == TestGetReport.REPORT_NAME
        assert report.columns
        assert any(
            row.get_cell("Email address").value == "bob.lee@acme.com"
            for row in report.rows
        )
        assert any(
            row.get_cell("Full Name").value == "David Ward" for row in report.rows
        )
        assert len(report.rows) > 100
        self.check_indexes(report)

    @pytest.mark.vcr("get_report.yaml")
    def test_get_report(self, smartsheet):
        report = smartsheet.reports.get(name=self.REPORT_NAME)
        self.check_report(report)

    @pytest.mark.asyncio
    @pytest.mark.vcr("get_report_async.yaml")
    async def test_get_report_async(self, async_smartsheet):
        report = await async_smartsheet.reports.get(name=self.REPORT_NAME)
        self.check_report(report)
