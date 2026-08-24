"""MCP tool registrations, split by domain."""

import functools
from typing import Callable


def tool_error_handler(format_error: Callable[[Exception], str]) -> Callable:
    """Build a decorator that routes any handler exception through ``format_error``.

    Apply it *under* ``@mcp.tool`` so FastMCP registers the wrapped callable::

        @mcp.tool(name="slipbox_create_note")
        @tool_error_handler(format_error)
        def slipbox_create_note(...): ...

    ``functools.wraps`` preserves the handler's signature, annotations, and
    docstring, which FastMCP introspects to build the tool schema. Tools that
    need bespoke handling (a tailored message, extra logging) can still add a
    narrow ``try``/``except`` inside the body; this only covers the common case
    of "surface any error to the caller".
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return format_error(e)

        return wrapper

    return decorator


def register_all_tools(server) -> None:
    """Register all MCP tools on the given server."""
    from slipbox_mcp.server.tools.cluster_tools import register_cluster_tools
    from slipbox_mcp.server.tools.link_tools import register_link_tools
    from slipbox_mcp.server.tools.note_tools import register_note_tools
    from slipbox_mcp.server.tools.search_tools import register_search_tools

    register_cluster_tools(server)
    register_link_tools(server)
    register_note_tools(server)
    register_search_tools(server)
