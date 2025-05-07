import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List

logger = logging.getLogger(__name__)

def extract_links_from_html(html_content: str, base_url: str) -> Set[str]:
    """
    Extracts all unique absolute links from HTML content.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links: Set[str] = set()
    
    base_domain = urlparse(base_url).netloc

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if not href or href.startswith('#') or href.lower().startswith('mailto:') or href.lower().startswith('tel:') or href.lower().startswith('javascript:'):
            continue

        try:
            # Construct absolute URL
            absolute_url = urljoin(base_url, href)
            parsed_absolute_url = urlparse(absolute_url)

            # Ensure it's a valid http/https URL and cleanup fragments
            if parsed_absolute_url.scheme in ['http', 'https']:
                # Optional: filter to stay on the same domain or subdomain
                # target_domain = urlparse(absolute_url).netloc
                # if not target_domain.endswith(base_domain): # Simple same-domain check
                #     logger.debug(f"Skipping external domain link: {absolute_url}")
                #     continue
                
                # Remove fragment
                absolute_url_no_fragment = parsed_absolute_url._replace(fragment="").geturl()
                links.add(absolute_url_no_fragment)
            else:
                logger.debug(f"Skipping non-http/https link: {absolute_url}")

        except Exception as e:
            logger.warning(f"Could not process link '{href}' from base '{base_url}': {e}")
            
    logger.debug(f"Extracted {len(links)} links from {base_url}")
    return links

# Example:
# async def crawl_recursively(start_url: str, depth: int, http_client, visited_urls: Set[str], process_url_callback):
#     """
#     A simplified recursive crawling function.
#     `process_url_callback` would be the main crawler's method to handle each URL.
#     """
#     if depth < 0 or start_url in visited_urls:
#         return
    
#     logger.info(f"Recursively crawling: {start_url} at depth {depth}")
#     visited_urls.add(start_url)

#     try:
#         # This part would be handled by MasterCrawler.fetch_page_content
#         response = await http_client.get(start_url)
#         response.raise_for_status()
#         html_content = response.text
        
#         # Call the main processing logic for the current URL (which might find files)
#         await process_url_callback(start_url, html_content, current_depth=(MAX_DEPTH - depth)) # Assuming MAX_DEPTH

#         if depth > 0: # Only extract and follow links if more depth is allowed
#             extracted_links = extract_links_from_html(html_content, start_url)
#             for link in extracted_links:
#                 await crawl_recursively(link, depth - 1, http_client, visited_urls, process_url_callback)

#     except httpx.RequestError as e:
#         logger.warning(f"Request error during recursive crawl of {start_url}: {e}")
#     except Exception as e:
#         logger.error(f"Error during recursive crawl of {start_url}: {e}", exc_info=True)


if __name__ == '__main__':
    sample_html = """
    <html><body>
        <a href="/page1.html">Page 1</a>
        <a href="https://external.com/other">External</a>
        <a href="sub/page2.html">Page 2</a>
        <a href="#section">Section Link</a>
        <a href="mailto:test@example.com">Mail</a>
        <a href="http://example.com/page1.html">Absolute Page 1 (same domain)</a>
        <a href="https://example.com/page3.html#fragment">Page 3 with fragment</a>
        <a href="javascript:void(0)">JS Link</a>
    </body></html>
    """
    base = "https://example.com/main/"
    extracted = extract_links_from_html(sample_html, base)
    print(f"Base URL: {base}")
    print("Extracted Links:")
    for link in extracted:
        print(link)
    
    # Expected:
    # https://example.com/main/page1.html
    # https://external.com/other
    # https://example.com/main/sub/page2.html
    # https://example.com/page1.html
    # https://example.com/page3.html
    
    print("\n--- Second Test ---")
    sample_html2 = '<a href="../another.html">Another</a> <a href="https://sub.example.com/test">Subdomain</a>'
    base2 = "https://example.com/one/two/"
    extracted2 = extract_links_from_html(sample_html2, base2)
    print(f"Base URL: {base2}")
    print("Extracted Links:")
    for link in extracted2:
        print(link)
    # Expected:
    # https://example.com/one/another.html
    # https://sub.example.com/test
