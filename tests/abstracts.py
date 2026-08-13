from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

import pytest
from httpx import AsyncClient, Response


class TestRoute(ABC):
    """Abstract base for route test classes that exercise HTTP endpoints.

    This base automatically attaches the shared async test client (`client`) and
    JWT token factory (`jwt_token`) for each collected test method.

    Child classes define the route metadata through `route_url` and implement
    `request_route` with the request details specific to that endpoint,
    including the chosen HTTP method.
    """

    route_url: str
    client: AsyncClient
    jwt_token: Callable[[str], Awaitable[str]]

    @pytest.fixture(autouse=True)
    def _setup(self, client, jwt_token):
        self.client = client
        self.jwt_token = jwt_token

    @abstractmethod
    async def request_route(self, **kwargs: Any) -> Response:
        raise NotImplementedError
