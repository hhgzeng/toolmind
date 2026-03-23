"""Session management for MCP (SSE only)."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Literal, Protocol

from mcp import ClientSession
from mcp.client.sse import sse_client
from typing_extensions import NotRequired, TypedDict

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    import httpx

DEFAULT_HTTP_TIMEOUT = 5
DEFAULT_SSE_READ_TIMEOUT = 60 * 5


class McpHttpClientFactory(Protocol):
    """Protocol for creating httpx.AsyncClient instances for MCP connections."""

    def __call__(
        self,
        headers: dict[str, str] | None = None,
        timeout: httpx.Timeout | None = None,
        auth: httpx.Auth | None = None,
    ) -> httpx.AsyncClient: ...


class SSEConnection(TypedDict):
    """Configuration for Server-Sent Events (SSE) transport connections to MCP."""

    transport: Literal["sse"]
    url: str

    headers: NotRequired[dict[str, Any] | None]
    timeout: NotRequired[float]
    sse_read_timeout: NotRequired[float]
    session_kwargs: NotRequired[dict[str, Any] | None]

    httpx_client_factory: NotRequired[McpHttpClientFactory | None]
    auth: NotRequired[httpx.Auth]


Connection = SSEConnection


@asynccontextmanager
async def create_session(connection: Connection) -> AsyncIterator[ClientSession]:
    """Create a new session to an MCP server (SSE only)."""
    transport = connection.get("transport")
    if transport != "sse":
        raise ValueError(f"Unsupported transport: {transport}. Must be 'sse'.")

    url = connection.get("url")
    if not url:
        raise ValueError("'url' parameter is required for SSE connection")

    headers = connection.get("headers")
    timeout = connection.get("timeout", DEFAULT_HTTP_TIMEOUT)
    sse_read_timeout = connection.get("sse_read_timeout", DEFAULT_SSE_READ_TIMEOUT)
    session_kwargs = connection.get("session_kwargs") or {}

    httpx_client_factory = connection.get("httpx_client_factory")
    auth = connection.get("auth")

    kwargs: dict[str, Any] = {}
    if httpx_client_factory is not None:
        kwargs["httpx_client_factory"] = httpx_client_factory

    async with (
        sse_client(url, headers, timeout, sse_read_timeout, auth=auth, **kwargs) as (
            read,
            write,
        ),
        ClientSession(read, write, **session_kwargs) as session,
    ):
        yield session


__all__ = ["Connection", "SSEConnection", "McpHttpClientFactory", "create_session"]
