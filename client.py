import requests


class BinaryLaneAPIError(Exception):
    """Base exception for BinaryLane API errors."""

    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class BinaryLaneAuthError(BinaryLaneAPIError):
    """Raised on 401 Unauthorized."""

    pass


class BinaryLaneNotFound(BinaryLaneAPIError):
    """Raised on 404 Not Found."""

    pass


class BinaryLaneValidationError(BinaryLaneAPIError):
    """Raised on 400 Bad Request or validation errors."""

    pass


class BinaryLaneClient:
    def __init__(self, api_token: str, base_url: str = "https://api.binarylane.com.au"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs) -> dict:
        if not path.startswith("/"):
            path = "/" + path
        url = f"{self.base_url}{path}"

        response = self.session.request(method, url, **kwargs)

        if response.status_code == 401:
            raise BinaryLaneAuthError(
                "Authentication failed. Check your API token.",
                status_code=401,
                response_data=response.text,
            )
        elif response.status_code == 404:
            raise BinaryLaneNotFound(
                f"Resource not found: {path}",
                status_code=404,
                response_data=response.text,
            )
        elif response.status_code == 400:
            raise BinaryLaneValidationError(
                "Validation error. Check your request.",
                status_code=400,
                response_data=response.text,
            )

        response.raise_for_status()

        if response.status_code == 204:
            return {}
        return response.json()

    # Account
    def get_account(self) -> dict:
        return self._request("GET", "/v2/account")

    # Servers
    def list_servers(self, page: int = 1, per_page: int = 20) -> dict:
        params = {"page": page, "per_page": per_page}
        return self._request("GET", "/v2/servers", params=params)

    def get_server(self, server_id: int) -> dict:
        return self._request("GET", f"/v2/servers/{server_id}")

    # Actions
    def list_actions(self, page: int = 1, per_page: int = 20) -> dict:
        params = {"page": page, "per_page": per_page}
        return self._request("GET", "/v2/actions", params=params)

    def perform_server_action(self, server_id: int, action_type: str, **kwargs) -> dict:
        payload = {"type": action_type, **kwargs}
        return self._request("POST", f"/v2/servers/{server_id}/actions", json=payload)

    # Helpers
    def get_server_list(self) -> list:
        """Convenience: returns just the list of server dicts."""
        data = self.list_servers()
        return data.get("servers", [])

    # Data Usage
    def get_data_usage(self, server_id: int) -> dict:
        return self._request("GET", f"/v2/data_usages/{server_id}/current")

    # Performance / Sample Sets
    def get_latest_sample_set(
        self, server_id: int, data_interval: str = "five-minute"
    ) -> dict:
        params = {"data_interval": data_interval}
        return self._request("GET", f"/v2/samplesets/{server_id}/latest", params=params)