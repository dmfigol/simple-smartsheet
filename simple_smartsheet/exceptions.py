import json
from typing import Optional

from requests import Response

from simple_smartsheet.models.extra import Error


class SmartsheetError(Exception):
    pass


class SmartsheetHTTPError(SmartsheetError):
    def __init__(self, http_response_code: int, error: Error = None, message: str = ""):
        result_msg_items = [f"HTTP response code {http_response_code}"]
        if error is not None:
            result_msg_items.append(f"Error code {error.error_code}")
            if error.message:
                message = error.message

        if message:
            result_msg_items.append(message)

        result_msg = " - ".join(result_msg_items)
        super().__init__(result_msg)

        self.http_response_code = http_response_code
        self.message = message
        self.error = error

    @classmethod
    def from_response(cls, response: Response):
        http_response_code = response.status_code
        error: Optional[Error] = None
        message = ""
        if response.text:
            try:
                error = Error.load(response.json())
            except json.JSONDecodeError:
                message = response.text

        if 400 <= http_response_code < 500:
            return SmartsheetHTTPClientError(http_response_code, error, message)
        elif 500 <= http_response_code < 600:
            return SmartsheetHTTPServerError(http_response_code, error, message)
        else:
            return cls(http_response_code, error, message)


class SmartsheetHTTPClientError(SmartsheetHTTPError):
    pass


class SmartsheetHTTPServerError(SmartsheetHTTPError):
    pass


class SmartsheetObjectNotFound(SmartsheetError):
    pass


class SmartsheetIndexNotFound(SmartsheetError):
    pass


class SmartsheetIndexNotUnique(SmartsheetError):
    pass
