import logging
import httpx
from typing import Optional, Dict, Any

from breachwatch.utils.config_loader import get_settings

logger = logging.getLogger(__name__)
config = get_settings()

DEFAULT_USER_AGENT = config.DEFAULT_USER_AGENT
DEFAULT_TIMEOUT = config.REQUEST_TIMEOUT


async def make_async_http_request(
    method: str,
    url: str,
    client: Optional[httpx.AsyncClient] = None, # Allow passing an existing client
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None, # For POST form data
    json_payload: Optional[Dict[str, Any]] = None, # For POST JSON data
    timeout: Optional[int] = DEFAULT_TIMEOUT,
    allow_redirects: bool = True,
    max_retries: int = 0 # Simple retry mechanism (0 means no retries beyond initial attempt)
) -> Optional[httpx.Response]:
    """
    Makes an asynchronous HTTP request with specified method and parameters.
    Includes basic retry logic.
    """
    effective_headers = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        effective_headers.update(headers)

    attempt = 0
    while attempt <= max_retries:
        try:
            if client: # Use passed client
                response = await client.request(
                    method, url, headers=effective_headers, params=params, data=data, json=json_payload, 
                    timeout=timeout, follow_redirects=allow_redirects
                )
            else: # Create a new client for a one-off request
                async with httpx.AsyncClient() as one_off_client:
                    response = await one_off_client.request(
                        method, url, headers=effective_headers, params=params, data=data, json=json_payload, 
                        timeout=timeout, follow_redirects=allow_redirects
                    )
            
            # response.raise_for_status() # Optional: raise exception for 4xx/5xx immediately
            return response
        
        except httpx.TimeoutException as e:
            logger.warning(f"Request to {url} timed out (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except httpx.RequestError as e: # Covers ConnectError, ReadError, etc.
            logger.warning(f"Request error for {url} (attempt {attempt + 1}/{max_retries + 1}): {e}")
        except Exception as e: # Catch-all for unexpected errors during request
            logger.error(f"Unexpected error during request to {url} (attempt {attempt + 1}/{max_retries + 1}): {e}", exc_info=True)
        
        attempt += 1
        if attempt <= max_retries:
            await asyncio.sleep(1 * attempt) # Exponential backoff (very basic)

    logger.error(f"Failed to get a successful response from {url} after {max_retries + 1} attempts.")
    return None


async def get_url_content(url: str, client: Optional[httpx.AsyncClient] = None, **kwargs) -> Optional[str]:
    """Helper to GET URL content as text."""
    response = await make_async_http_request("GET", url, client=client, **kwargs)
    if response and response.status_code == 200:
        try:
            return response.text
        except Exception as e:
            logger.error(f"Error decoding text content from {url}: {e}")
            # Try to decode with a different encoding if common
            try:
                return response.content.decode('latin-1', errors='replace')
            except Exception:
                 return response.content.decode('utf-8', errors='replace') # Final fallback

    elif response:
        logger.warning(f"GET request to {url} failed with status {response.status_code}")
    return None

async def get_url_bytes(url: str, client: Optional[httpx.AsyncClient] = None, **kwargs) -> Optional[bytes]:
    """Helper to GET URL content as bytes."""
    response = await make_async_http_request("GET", url, client=client, **kwargs)
    if response and response.status_code == 200:
        return response.content
    elif response:
        logger.warning(f"GET request for bytes from {url} failed with status {response.status_code}")
    return None


# Example Usage (requires an async context)
if __name__ == "__main__":
    import asyncio

    async def main():
        # Test GET text
        test_text_url = "https://httpbin.org/get"
        content = await get_url_content(test_text_url)
        if content:
            print(f"Content from {test_text_url} (first 100 chars): {content[:100]}")
        else:
            print(f"Failed to get content from {test_text_url}")

        # Test GET bytes (e.g., an image or binary file)
        # Using a small public image for test
        test_bytes_url = "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
        img_bytes = await get_url_bytes(test_bytes_url)
        if img_bytes:
            print(f"Got {len(img_bytes)} bytes from {test_bytes_url}")
        else:
            print(f"Failed to get bytes from {test_bytes_url}")

        # Test with retries (simulating a temporarily failing URL)
        failing_url = "https://httpbin.org/status/503" # This URL returns 503
        print(f"\nTesting retries for {failing_url}...")
        failed_response = await make_async_http_request("GET", failing_url, max_retries=2)
        if failed_response:
            print(f"Response from failing_url: Status {failed_response.status_code}")
        else:
            print(f"No response from failing_url after retries.")

    asyncio.run(main())
