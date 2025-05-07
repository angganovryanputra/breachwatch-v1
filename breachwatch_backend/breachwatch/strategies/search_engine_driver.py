import logging
import httpx
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse, parse_qs
from typing import AsyncGenerator, Optional, List, Set

logger = logging.getLogger(__name__)

# Basic configuration for a few search engines
# This is highly simplified and may need proxies, CAPTCHA solving, and more robust parsing in a real scenario.
SEARCH_ENGINES_CONFIG = {
    "google": {
        "url_template": "https://www.google.com/search?q={query}&num={num_results}&start={start_index}",
        "link_selector": "div.g a",  # This selector is highly volatile for Google
        "href_attribute": "href",
        "next_page_logic": None, # Google uses 'start' parameter
        "results_per_page": 10 # Approximate, can vary
    },
    "bing": {
        "url_template": "https://www.bing.com/search?q={query}&count={num_results}&first={start_index}",
        "link_selector": "li.b_algo h2 a", # Volatile
        "href_attribute": "href",
        "next_page_logic": None, # Bing uses 'first' parameter
        "results_per_page": 10
    },
    "duckduckgo": { # DDG is often more friendly to scraping but has HTML and JS versions
        "url_template": "https://html.duckduckgo.com/html/?q={query}", # Using HTML version
        "link_selector": "a.result__a", # Volatile
        "href_attribute": "href",
        "next_page_logic": "form.results_form_next input[type=submit]", # Check for next page form
        "results_per_page": 30 # Approximate
    }
}
# Default to DuckDuckGo as it's generally more scraper-friendly, though results might differ.
DEFAULT_SEARCH_ENGINE = "duckduckgo"

async def execute_dork(
    dork_query: str,
    http_client: httpx.AsyncClient,
    max_results: int = 20,
    search_engine_name: str = DEFAULT_SEARCH_ENGINE
) -> AsyncGenerator[str, None]:
    """
    Executes a search dork on a specified search engine and yields result URLs.
    This is a very basic implementation and prone to being blocked.
    """
    if search_engine_name not in SEARCH_ENGINES_CONFIG:
        logger.error(f"Search engine '{search_engine_name}' not configured.")
        return

    config = SEARCH_ENGINES_CONFIG[search_engine_name]
    collected_urls: Set[str] = set()
    
    # DuckDuckGo HTML doesn't paginate with num_results/start_index easily in the same way
    # It loads more results on a single page or via form submission for "More results"
    # For DDG HTML, we might just fetch one page and parse, as it tends to give a good number of results.
    # Or implement form submission for "More results" if needed.
    
    num_fetched_this_dork = 0
    current_page = 0 # For engines that use page numbers or start indices

    # Simplified for DDG HTML, might need adjustments for Google/Bing pagination
    if search_engine_name == "duckduckgo":
        search_url = config["url_template"].format(query=quote_plus(dork_query))
        try:
            logger.debug(f"Fetching Dork URL (DDG): {search_url}")
            response = await http_client.get(search_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0"}) # More common UA
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links_found_on_page = 0
            for link_tag in soup.select(config["link_selector"]):
                href = link_tag.get(config["href_attribute"])
                if href:
                    # DDG links can be relative or wrapped, e.g., /l/?kh=-1&uddg=https%3A%2F%2Fexample.com
                    parsed_href = urlparse(href)
                    if parsed_href.path == "/l/" and parsed_href.query:
                        query_params = parse_qs(parsed_href.query)
                        if 'uddg' in query_params and query_params['uddg']:
                            actual_url = query_params['uddg'][0]
                            if actual_url not in collected_urls and not actual_url.startswith("duckduckgo.com"):
                                logger.debug(f"Dork result (DDG): {actual_url}")
                                yield actual_url
                                collected_urls.add(actual_url)
                                num_fetched_this_dork += 1
                                links_found_on_page +=1
                                if num_fetched_this_dork >= max_results:
                                    return # Reached max requested results for this dork
                    elif not parsed_href.netloc.endswith("duckduckgo.com") and href not in collected_urls:
                         logger.debug(f"Dork result (DDG direct): {href}")
                         yield href
                         collected_urls.add(href)
                         num_fetched_this_dork += 1
                         links_found_on_page +=1
                         if num_fetched_this_dork >= max_results:
                            return
            
            if links_found_on_page == 0:
                 logger.info(f"No links found on DDG for dork: {dork_query} using selector {config['link_selector']}")


        except httpx.RequestError as e:
            logger.warning(f"Request error during dork execution for '{dork_query}': {e}")
        except httpx.HTTPStatusError as e:
            logger.warning(f"HTTP status {e.response.status_code} for dork '{dork_query}': {e.response.text[:200]}")
        except Exception as e:
            logger.error(f"Unexpected error processing dork '{dork_query}': {e}", exc_info=True)
    else:
        # Placeholder for Google/Bing logic which is much harder due to anti-bot measures
        logger.warning(f"Search engine '{search_engine_name}' dork execution is not fully implemented due to anti-scraping measures. Using DDG is more reliable for basic cases.")
        # If implementing Google/Bing:
        # Loop through pages:
        #   Calculate start_index or page number
        #   Format search_url = config["url_template"].format(query=quote_plus(dork_query), num_results=config["results_per_page"], start_index=...)
        #   Fetch, parse, yield URLs
        #   Check for next page indicators or if num_fetched_this_dork >= max_results

# Example (conceptual)
# async def main():
#     async with httpx.AsyncClient() as client:
#         dork = 'filetype:sql "passwords"'
#         print(f"Executing dork: {dork}")
#         async for url in execute_dork(dork, client, max_results=5):
#             print(f"Found URL: {url}")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
