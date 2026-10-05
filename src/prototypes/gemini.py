import logging
import time
from collections.abc import Callable
from typing import TypeVar

from google.genai.errors import ServerError

T = TypeVar("T")
logger = logging.getLogger(__name__)


def generate_content_with_retry(generate: Callable[[], T]) -> T:
    """Retry Gemini's transient 503 responses with bounded exponential backoff."""
    retry_delays = (2, 4, 8)

    for attempt, delay in enumerate((*retry_delays, None), start=1):
        try:
            return generate()
        except ServerError as error:
            if error.code != 503 or delay is None:
                raise

            logger.warning(
                "Gemini returned 503; retrying in %s seconds (attempt %s of %s).",
                delay,
                attempt,
                len(retry_delays) + 1,
            )
            time.sleep(delay)

    raise RuntimeError("Gemini retry loop exited unexpectedly.")
