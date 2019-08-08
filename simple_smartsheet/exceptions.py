import json
from typing import Optional, TypeVar, Type

from aiohttp import ClientResponse
from requests import Response

from simple_smartsheet.models.extra import Error


class SmartsheetError(Exception):
    pass


T = TypeVar("T", bound="SmartsheetHTTPError")


class SmartsheetHTTPError(SmartsheetError):
    def __init__(self, status_code: int, error: Error = None, message: str = ""):
        result_msg_items = [f"HTTP response code {status_code}"]
        if error is not None:
            result_msg_items.append(f"Error code {error.error_code}")
            if error.message:
                message = error.message

        if message:
            result_msg_items.append(message)

        result_msg = " - ".join(result_msg_items)
        super().__init__(result_msg)

        self.status_code = status_code
        self.message = message
        self.error = error

    @classmethod
    def _from_response_data(
        cls: Type[T], status_code: int, response_text: str
    ) -> "SmartsheetHTTPError":
        error: Optional[Error] = None
        message = ""

        if response_text:
            try:
                response_json = json.loads(response_text)
                error = Error.load(response_json)
            except json.JSONDecodeError:
                message = response_text

        if 400 <= status_code < 500:
            if status_code == 404:
                return SmartsheetHTTPObjectNotFound(status_code, error, message)
            else:
                return SmartsheetHTTPClientError(status_code, error, message)
        elif 500 <= status_code < 600:
            return SmartsheetHTTPServerError(status_code, error, message)
        else:
            return cls(status_code, error, message)

    @classmethod
    def from_response(cls: Type[T], response: Response) -> "SmartsheetHTTPError":
        response_text = response.text
        status_code = response.status_code
        return cls._from_response_data(status_code, response_text)

    @classmethod
    async def from_async_response(
        cls: Type[T], response: ClientResponse
    ) -> "SmartsheetHTTPError":
        response_text = await response.text()
        status_code = response.status
        return cls._from_response_data(status_code, response_text)


class SmartsheetHTTPClientError(SmartsheetHTTPError):
    pass


class SmartsheetHTTPObjectNotFound(SmartsheetHTTPClientError):
    pass


class SmartsheetHTTPServerError(SmartsheetHTTPError):
    pass


class SmartsheetObjectNotFound(SmartsheetError):
    pass


class SmartsheetIndexNotFound(SmartsheetError):
    pass


class SmartsheetIndexNotUnique(SmartsheetError):
    pass
