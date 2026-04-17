"""
Retry logic for LLM calls using exponential backoff.
Handles transient errors like rate limits and timeouts.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from config import MAX_RETRIES, RETRY_BACKOFF_MULTIPLIER, RETRY_MIN_WAIT, RETRY_MAX_WAIT


def llm_retry_decorator(func):
    """
    Decorator for LLM calls with exponential backoff retry logic.
    Retries on transient errors (timeouts, rate limits).
    
    Usage:
        @llm_retry_decorator
        def call_llm(llm, prompt):
            return llm.invoke(prompt)
    """
    return retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(
            multiplier=RETRY_BACKOFF_MULTIPLIER,
            min=RETRY_MIN_WAIT,
            max=RETRY_MAX_WAIT,
        ),
        retry=retry_if_exception_type((
            TimeoutError,
            ConnectionError,
            Exception,  # Catch all for rate limit errors
        )),
        reraise=True,
    )(func)
