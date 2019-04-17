from typing import Optional, Dict, Any, Union

import requests

from simple_smartsheet import constants
from simple_smartsheet import exceptions
from simple_smartsheet.types import JSONType
from simple_smartsheet.models.extra import Result
from simple_smartsheet.models.report import ReportCRUD
from simple_smartsheet.models.sheet import SheetCRUD


class Smartsheet:
    """Smartsheet API class that provides a way to interact with Smartsheet objects.

    Attributes:
        token: Smartsheet API token, obtained in Personal Settings -> API access
        session: requests.Session object which stores headers based on the token
        sheets: SheetsCRUD object which provides methods to interact with Sheets
    """

    API_HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}

    def __init__(self, token: str) -> None:
        self.session = requests.Session()
        self.token = token

        self.sheets = SheetCRUD(self)
        self.reports = ReportCRUD(self)

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value) -> None:
        self._token = value
        # when the token is changed, update headers too
        self._update_headers()

    def _update_headers(self) -> None:
        """Updates HTTP Headers with the token"""
        headers = {"Authorization": f"Bearer {self.token}", **self.API_HEADERS}
        self.session.headers.update(headers)

    @staticmethod
    def get_endpoint_url(endpoint: str) -> str:
        """Build a full API url based on the relative API path.

        For example:
            get_endpoint_url('/sheets') -> 'https://api.smartsheet.com/2.0/sheets'
        """
        return constants.API_ROOT + endpoint

    def get(
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
        url = self.get_endpoint_url(endpoint)
        response = self.session.get(url, params=params)
        if response.ok:
            if response.text:
                response_json = response.json()
                if path:
                    if path in response_json:
                        return response_json[path]
                    raise AttributeError(
                        f"Response from GET {url} does not contain key {path!r}"
                    )
                else:
                    return response_json
            else:
                return {}
        else:
            raise exceptions.SmartsheetHTTPError.from_response(response)

    def post(
        self, endpoint: str, data: Optional[JSONType] = None, result_obj: bool = True
    ) -> Union[Result, Dict[str, Any], None]:
        """Performs HTTP POST on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            data: dictionary or list with data that is going to be sent as JSON
            result_obj: whether to convert received JSON response to Result object

        Returns:
            Result object
        """
        url = self.get_endpoint_url(endpoint)

        if data:
            response = self.session.post(url, json=data)
        else:
            response = self.session.post(url)
        if response.ok:
            if response.text:
                json_response = response.json()
                if result_obj:
                    result = Result.load(json_response)
                    return result
                else:
                    return json_response
            else:
                return None
        else:
            raise exceptions.SmartsheetHTTPError.from_response(response)

    def put(self, endpoint: str, data: JSONType) -> Optional[Result]:
        """Performs HTTP PUT on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            data: dictionary or list with data that is going to be sent as JSON

        Returns:
            Result object
        """
        url = self.get_endpoint_url(endpoint)

        response = self.session.put(url, json=data)
        if response.ok:
            result = Result.load(response.json())
            return result
        else:
            raise exceptions.SmartsheetHTTPError.from_response(response)

    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Result:
        """Performs HTTP DELETE on the endpoint

        Args:
            endpoint: relative API endpoint, for example '/sheets'
            params: HTTP query params dictionary

        Returns:
            Result object
        """
        url = self.get_endpoint_url(endpoint)

        response = self.session.delete(url, params=params)
        if response.ok:
            result = Result.load(response.json())
            return result
        else:
            raise exceptions.SmartsheetHTTPError.from_response(response)
