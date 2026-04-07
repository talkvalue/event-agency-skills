"""Event Agency Skills — shared libraries."""

from lib.event_context import EventContext, EventPhase

try:
    from lib.composio_client import EventComposioClient
except ImportError:
    EventComposioClient = None

__all__ = ["EventComposioClient", "EventContext", "EventPhase"]
