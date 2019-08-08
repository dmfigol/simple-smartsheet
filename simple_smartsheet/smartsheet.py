import json
from typing import Optional, Dict, Any, Union, cast

import aiohttp
import requests

from simple_smartsheet import constants
from simple_smartsheet import exceptions
from simple_smartsheet.types import JSONType
from simple_smartsheet.models.extra import Result
from simple_smartsheet.models.report import ReportCRUD, ReportAsyncCRUD
from simple_smartsheet.models.sheet import SheetCRUD, SheetAsyncCRUD


class SmartsheetBase:
    """Smartsheet API class that provides a way to interact with Smartsheet objects.

    Attributes:
        token: Smartsheet API token, obtained in Personal Settings -> API access
    """

    API_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

    def __init__(self, token: str) -> None:

        self.token = token

    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.token}", **self.API_HEADERS}

    @staticmethod
    def build_url(endpoint: str) -> str:
        """Build a full API url based on the relative API path.

        For example:
            build_url('/sheets') -> 'https://api.smartsheet.com/2.0/sheets'
        """
        return constants.API_ROOT + endpoint

    @staticmethod
    def _process_response_text(
        response_text: Optional[str] = None,
        response_path: Optional[str] = None,
        result_obj: bool = False,
    ) -> Union[None, Result, JSONType]:
        if not response_text:
            return None
        response_data = json.loads(response_text)
        if response_path is not None:
            response_data = response_data[response_path]
        if result_obj:
            result = Result.load(response_data)
            return result
        else:
            return response_data


class Smartsheet(SmartsheetBase):
    """Smartsheet API class that provides a way to interact with Smartsheet objects.

    Attributes:
        token: Smartsheet API token, obtained in Personal Settings -> API access
        _session: requests.Session object which stores headers based on the token
        sheets: SheetsCRUD object which provides methods to interact with Sheets
    """

    API_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

    def __init__(self, token: str) -> None:
        super().__init__(token)

        self._session = requests.Session()
        self._session.headers.update(**self._headers)

        self.sheets = SheetCRUD(self)
        self.reports = ReportCRUD(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.close()

    def close(self) -> None:
        self._session.close()

    def _request(
        self,
        method: str,
        endpoint: str,
        response_path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[JSONType] = None,
        result_obj: bool = False,
    ) -> Union[None, Result, JSONType]:
        url = self.build_url(endpoint)
        response = self._session.request(
            method=method, url=url, params=params, json=data
        )
        if not response.ok:
            raise exceptions.SmartsheetHTTPError.from_response(response)
        else:
            response_text = response.text
            return self._process_response_text(response_text, response_path, result_obj)

    def _get(
        self,
        endpoint: str,
        path: Optional[str] = "data",
        params: Optional[Dict[str, Any]] = None,
    ) -> JSONType:
        """Performs HTTP GET on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            path: in response extract the data under the specific path.
                Default - 'data'. Specify None if not needed
            params: HTTP query params dictionary

        Returns:
            JSON data from the response, under the specific key.
        """
        result = self._request("GET", endpoint, response_path=path, params=params)
        return cast(JSONType, result)

    def _post(
        self, endpoint: str, data: Optional[JSONType] = None, result_obj: bool = True
    ) -> Result:
        """Performs HTTP POST on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            data: dictionary or list with data that is going to be sent as JSON
            result_obj: whether to convert received JSON response to Result object

        Returns:
            Result object
        """
        result = self._request("POST", endpoint, data=data, result_obj=result_obj)
        return cast(Result, result)

    def _put(self, endpoint: str, data: JSONType) -> Result:
        """Performs HTTP PUT on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            data: dictionary or list with data that is going to be sent as JSON

        Returns:
            Result object
        """
        result = self._request("PUT", endpoint, data=data, result_obj=True)
        return cast(Result, result)

    def _delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Result:
        """Performs HTTP DELETE on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            params: HTTP query params dictionary

        Returns:
            Result object
        """
        result = self._request("DELETE", endpoint, params=params, result_obj=True)
        return cast(Result, result)


class AsyncSmartsheet(SmartsheetBase):
    def __init__(self, token: str) -> None:
        super().__init__(token)

        self._session = aiohttp.ClientSession()
        self._session._default_headers.update(**self._headers)

        self.sheets = SheetAsyncCRUD(self)
        self.reports = ReportAsyncCRUD(self)

    async def close(self) -> None:
        await self._session.close()

    async def __aenter__(self) -> "AsyncSmartsheet":
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    def __enter__(self):
        raise NotImplementedError(
            "Use 'async with AsyncSmartsheet', instead of 'with AsyncSmartsheet'"
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        response_path: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[JSONType] = None,
        result_obj: bool = False,
    ) -> Union[None, Result, JSONType]:
        url = self.build_url(endpoint)
        async with self._session.request(
            method=method, url=url, params=params, json=data
        ) as response:
            if response.status >= 400:
                raise await exceptions.SmartsheetHTTPError.from_async_response(response)
            response_text = await response.text()
            return self._process_response_text(response_text, response_path, result_obj)

    async def _get(
        self,
        endpoint: str,
        path: Optional[str] = "data",
        params: Optional[Dict[str, Any]] = None,
    ) -> JSONType:
        """Performs HTTP GET on the endpoint asynchronously

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            path: in response extract the data under the specific path.
                Default - 'data'. Specify None if not needed
            params: HTTP query params dictionary

        Returns:
            JSON data from the response, under the specific key.
        """
        result = await self._request("GET", endpoint, response_path=path, params=params)
        return cast(JSONType, result)

    async def _post(
        self, endpoint: str, data: Optional[JSONType] = None, result_obj: bool = True
    ) -> Union[Result, JSONType, None]:
        """Performs HTTP POST on the endpoint asynchronously

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            data: dictionary or list with data that is going to be sent as JSON
            result_obj: whether to convert received JSON response to Result object

        Returns:
            Result object
        """
        result = await self._request("POST", endpoint, data=data, result_obj=result_obj)
        return result

    async def _put(self, endpoint: str, data: JSONType) -> Optional[Result]:
        """Performs HTTP PUT on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            data: dictionary or list with data that is going to be sent as JSON

        Returns:
            Result object
        """
        result = await self._request("PUT", endpoint, data=data, result_obj=True)
        return cast(Optional[Result], result)

    async def _delete(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Result:
        """Performs HTTP DELETE on the endpoint asynchronously

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            params: HTTP query params dictionary

        Returns:
            Result object
        """
        result = await self._request("DELETE", endpoint, params=params, result_obj=True)
        return cast(Result, result)
