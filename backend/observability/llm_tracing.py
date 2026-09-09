"""Optional self-hosted Langfuse traces. Content is not exported by default."""

from contextlib import contextmanager
from backend.config import settings


@contextmanager
def observation(name):
    if not settings.enable_langfuse:
        yield None
        return
    from langfuse import get_client

    with get_client().start_as_current_observation(as_type="span", name=name) as span:
        yield span
