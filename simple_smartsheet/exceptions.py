class SmartsheetHTTPError(Exception):
    def __init__(self, http_response_code: int, error_code: int, message: str):
        result_msg = (
            f"HTTP response code {http_response_code} - "
            f"Error code {error_code} - {message}"
        )
        super().__init__(result_msg)
        self.message = message
        self.error_code = error_code
        self.http_response_code = http_response_code
