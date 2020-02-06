from simple_smartsheet.models import Sheet


class TestSheet:
    def test_dataframe(self, mocked_sheet: Sheet) -> None:
        df = mocked_sheet.as_dataframe()
        assert len(df) == 3
        assert df.loc[0]["Full Name"] == "Bob Lee"
        assert df.loc[1]["Email address"] == "alice.smith@globex.com"
        assert df.loc[2]["Company"] == "ACME"
        assert set(df.loc[2]["Maintains"]) == {"napalm", "netmiko", "nornir"}
