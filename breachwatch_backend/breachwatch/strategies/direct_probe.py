import logging
import httpx
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

async def probe_url(url: str, http_client: httpx.AsyncClient) -> Optional[Tuple[int, Optional[str]]]:
    """
    Directly probes a URL to check its status and content type.
    Returns (status_code, content_type_header) or None if request fails.
    """
    try:
        logger.debug(f"Probing URL: {url}")
        # Use HEAD request to be lighter if we only need headers
        # response = await http_client.head(url, timeout=5) 
        # However, some servers don't handle HEAD well, or we might need a snippet of content later.
        # For now, using GET but not reading full body unless needed.
        
        async with http_client.stream("GET", url, timeout=10) as response: # Stream to avoid downloading large files unnecessarily
            try:
                response.raise_for_status() # Check for 4xx/5xx errors
                content_type = response.headers.get("content-type", "").lower()
                logger.info(f"URL {url} probed successfully: Status {response.status_code}, Content-Type: {content_type}")
                return response.status_code, content_type
            except httpx.HTTPStatusError as e:
                logger.warning(f"Direct probe HTTP status error for {url}: {e.response.status_code}")
                return e.response.status_code, e.response.headers.get("content-type", "").lower()


    except httpx.RequestError as e:
        logger.warning(f"Direct probe request error for {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during direct probe of {url}: {e}", exc_info=True)
        return None

# Example usage:
# async def main():
#     async with httpx.AsyncClient() as client:
#         urls_to_probe = [
#             "https://example.com/somefile.txt", # Assume this exists
#             "https://example.com/nonexistent.zip", # Assume this doesn't
#             "https://google.com" 
#         ]
#         for url in urls_to_probe:
#             result = await probe_url(url, client)
#             if result:
#                 status, content_type = result
#                 print(f"URL: {url}, Status: {status}, Content-Type: {content_type}")
#             else:
#                 print(f"URL: {url}, Probe failed or error.")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
