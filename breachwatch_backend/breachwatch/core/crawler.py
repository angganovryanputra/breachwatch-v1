
import logging
import asyncio
import httpx # Modern async HTTP client, preferred over requests for async code
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote # Added unquote
from typing import List, Set, Optional, Tuple, Dict, AsyncGenerator, Union
from datetime import datetime, timezone
import re
import time
import random
import uuid
import xml.etree.ElementTree as ET # For parsing sitemaps
from urllib.robotparser import RobotFileParser


from breachwatch.api.v1 import schemas # For type hinting if needed for settings
from breachwatch.utils.config_loader import get_settings
from breachwatch.core import file_identifier, keyword_matcher, downloader
from breachwatch.strategies import search_engine_driver, direct_probe, recursive # direct_probe and recursive are now less directly used from here
from breachwatch.storage import crud, models # Import models
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)
config_settings = get_settings() # Global settings from config_loader

# List of common user agents for rotation
COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
    config_settings.DEFAULT_USER_AGENT # Default from config
]

class DomainLimiter:
    """Limits requests to a specific domain to respect politeness policies."""
    def __init__(self, delay_seconds: float, max_concurrent: int):
        self.delay_seconds = delay_seconds
        self.max_concurrent = max_concurrent
        self.last_request_time: float = 0
        self.active_requests: int = 0
        self._lock = asyncio.Lock()
        self._condition = asyncio.Condition(self._lock) # Condition for efficient waiting
        logger.debug(f"DomainLimiter initialized with delay: {delay_seconds}s, max_concurrent: {max_concurrent}")

    async def acquire(self):
        async with self._lock:
            while self.active_requests >= self.max_concurrent:
                logger.debug(f"DomainLimiter: Max concurrent ({self.max_concurrent}) reached for domain, waiting...")
                await self._condition.wait() # Wait until notified

            current_time = time.monotonic()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.delay_seconds:
                wait_time = self.delay_seconds - time_since_last_request
                logger.debug(f"DomainLimiter: Delaying for {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            self.last_request_time = time.monotonic()
            self.active_requests += 1
            logger.debug(f"DomainLimiter: Acquired. Active requests: {self.active_requests}")

    async def release(self):
        async with self._lock:
            self.active_requests -= 1
            logger.debug(f"DomainLimiter: Released. Active requests: {self.active_requests}")
            self._condition.notify() # Notify one waiting task


class MasterCrawler:
    """
    Orchestrates the crawling process. Includes proxy support, User-Agent rotation, 
    robots.txt respect, sitemap parsing, and referrer spoofing.
    """
    def __init__(self, job_id: uuid.UUID, crawl_settings: schemas.CrawlSettingsSchema, db: Session):
        self.job_id = job_id
        self.settings = crawl_settings # Per-job settings
        self.db = db
        self.visited_urls: Set[str] = set()
        self.domain_limiters: Dict[str, DomainLimiter] = {}
        
        self.user_agents = COMMON_USER_AGENTS
        if self.settings.custom_user_agent: # Prepend custom UA if provided
            self.user_agents = [self.settings.custom_user_agent] + self.user_agents
        
        self.request_timeout = config_settings.REQUEST_TIMEOUT # Global timeout
        self._should_stop_event = asyncio.Event()
        self.initial_urls_found = False
        
        self.robots_parsers_cache: Dict[str, Optional[RobotFileParser]] = {}
        self.processed_sitemap_urls: Set[str] = set()

        # Proxy settings from the job's configuration
        self.proxies: Optional[List[str]] = self.settings.proxies if self.settings.proxies else None
        self.proxy_rotation_strategy: str = "random" # For now, only random for per-job proxies
        self.current_proxy_index: int = 0 # For sequential rotation if implemented later

        if self.proxies:
            logger.info(f"Job {self.job_id} will use {len(self.proxies)} proxies with '{self.proxy_rotation_strategy}' rotation.")

        # HTTP client setup - proxies will be applied per request or by creating new client instances
        # Default limits, can be tuned
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100) 
        # Base client without proxy, proxy will be configured per request or by recreating client
        self.http_client_no_proxy = httpx.AsyncClient(
            timeout=self.request_timeout,
            follow_redirects=True,
            limits=limits,
            verify=False # TODO: Make SSL verification configurable
        )
        # The actual client used for requests, potentially configured with a proxy
        self.http_client = self.http_client_no_proxy 
        
        logger.info(f"MasterCrawler for job {self.job_id} initialized. Respect robots.txt: {self.settings.respect_robots_txt}")
        logger.info(f"Keywords: {self.settings.keywords[:5]}..., Extensions: {self.settings.file_extensions[:5]}...")
        logger.info(f"Crawl Depth: {self.settings.crawl_depth}, Dorks: {len(self.settings.search_dorks)}")
        logger.info(f"Request Delay: {self.settings.request_delay_seconds}s, Max Concurrent per Domain: {self.settings.max_concurrent_requests_per_domain}")


    def _get_random_user_agent(self) -> str:
        return random.choice(self.user_agents)

    def _get_current_proxy(self) -> Optional[str]:
        """Selects a proxy based on the rotation strategy."""
        if not self.proxies:
            return None
        
        if self.proxy_rotation_strategy == "random":
            return random.choice(self.proxies)
        # Add other strategies like "sequential" if needed
        # elif self.proxy_rotation_strategy == "sequential":
        #     proxy = self.proxies[self.current_proxy_index % len(self.proxies)]
        #     self.current_proxy_index += 1
        #     return proxy
        return random.choice(self.proxies) # Default to random

    async def _get_http_client_with_proxy(self) -> httpx.AsyncClient:
        """Returns an HTTP client, configured with a proxy if available."""
        proxy_url = self._get_current_proxy()
        if proxy_url:
            proxies_dict = {"http://": proxy_url, "https://": proxy_url}
            logger.debug(f"Using proxy: {proxy_url} for next request.")
            # Creating a new client instance per request with proxy might be less efficient
            # than managing a pool, but simpler for now.
            # Consider if httpx.AsyncClient can have proxy set per request without re-creation.
            # `httpx.request` method accepts a `proxies` argument.
            # For simplicity, we'll build a client for each request needing proxy, or use one with default proxy.
            # Let's try to use one client and set proxy per request if `fetch_page_content` takes client as arg
            # For now, we re-create if proxy is different or first time
            # This part is tricky, httpx.AsyncClient itself can take proxies arg.
            # If we want to rotate, best is to pass proxy string to client.request()
            # If self.http_client is just a base one, then each request can specify a proxy.
            # Let's assume self.http_client is the one to use, and we configure its proxy if needed.
            # This logic might be better inside fetch_page_content itself.
            # For now, this method is conceptual. The actual proxy application happens in fetch_page_content.
            return httpx.AsyncClient(
                proxies=proxies_dict,
                timeout=self.request_timeout,
                follow_redirects=True,
                verify=False # TODO: Configurable SSL verification
            )
        return self.http_client_no_proxy # Return base client if no proxy

    async def _check_if_stopped(self) -> bool:
        """Checks if the stop signal has been received or job status is 'stopping'."""
        if self._should_stop_event.is_set():
            return True
        # Periodically check DB status for external stop signals
        if random.randint(1, 100) > 95: # Check DB status occasionally (e.g., 5% of the time)
            try:
                # Detach the job object from the current session if it's there to get fresh status
                # self.db.expire(job_object_if_any) 
                job_status_from_db = crud.get_crawl_job_status_only(self.db, self.job_id) # New CRUD needed
                if job_status_from_db == "stopping":
                    self._should_stop_event.set()
                    logger.info(f"Job {self.job_id} stop signal received via DB status 'stopping'.")
                    return True
            except SQLAlchemyError as db_err:
                 logger.error(f"Database error checking job status for {self.job_id}: {db_err}", exc_info=False) # Less verbose
            except Exception as e:
                 logger.error(f"Unexpected error checking job status for {self.job_id}: {e}", exc_info=False)
        return False

    async def stop_crawler(self):
        """Signals the crawler to stop gracefully."""
        if not self._should_stop_event.is_set():
            logger.info(f"MasterCrawler for job {self.job_id} received stop signal.")
            self._should_stop_event.set()
            try:
                # This might fail if called from a different thread/async context without a proper DB session
                # Ensure DB operations are safe if this method is called externally
                crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="stopping")
                self.db.commit()
            except Exception as e:
                 logger.error(f"Failed to update job {self.job_id} status to 'stopping' in DB after signal: {e}")
                 self.db.rollback()

    async def _get_domain_limiter(self, url: str) -> DomainLimiter:
        try:
            domain = urlparse(url).netloc
            if not domain: domain = "__no_domain__" # Handle URLs without a clear domain (e.g. file://)
        except ValueError: domain = "__parse_error__"
        if domain not in self.domain_limiters:
            self.domain_limiters[domain] = DomainLimiter(
                delay_seconds=self.settings.request_delay_seconds,
                max_concurrent=self.settings.max_concurrent_requests_per_domain or 2
            )
        return self.domain_limiters[domain]

    async def _fetch_robots_txt_parser(self, domain_url_str: str) -> Optional[RobotFileParser]:
        parsed_domain_url = urlparse(domain_url_str)
        domain_base = f"{parsed_domain_url.scheme}://{parsed_domain_url.netloc}"
        robots_url = urljoin(domain_base, "/robots.txt")

        if domain_base in self.robots_parsers_cache:
            # logger.debug(f"Using cached robots.txt parser for {domain_base}")
            return self.robots_parsers_cache[domain_base]

        logger.info(f"Fetching robots.txt from {robots_url}")
        parser = RobotFileParser()
        parser.set_url(robots_url)
        
        current_ua_for_robots = self._get_random_user_agent()
        # No proxy for robots.txt to avoid issues with proxy-specific blocks on robots.txt itself
        try:
            response = await self.http_client_no_proxy.get(robots_url, headers={"User-Agent": current_ua_for_robots}, timeout=self.request_timeout / 2)
            if response.status_code == 200:
                content = await response.text()
                parser.parse(content.splitlines())
                self.robots_parsers_cache[domain_base] = parser
                logger.info(f"Successfully fetched and parsed robots.txt for {domain_base}")
                return parser
            elif response.status_code == 404:
                 logger.info(f"No robots.txt found (404) for {domain_base}. Allowing all.")
                 self.robots_parsers_cache[domain_base] = None 
                 return None 
            else:
                logger.warning(f"Failed to fetch robots.txt for {domain_base}, status: {response.status_code}. Assuming allow for this path.")
                return None 
        except Exception as e:
            logger.error(f"Error fetching/parsing robots.txt for {domain_base}: {e}. Assuming allow.", exc_info=False)
            return None

    async def is_allowed_by_robots(self, url: str, user_agent_to_check: str) -> bool:
        if not self.settings.respect_robots_txt:
            return True
        
        parser = await self._fetch_robots_txt_parser(url)
        if parser is None:
            return True 
        
        is_allowed = parser.can_fetch(user_agent_to_check, url)
        logger.debug(f"Robots.txt check for '{url}' with UA '{user_agent_to_check}': {'Allowed' if is_allowed else 'Disallowed'}")
        return is_allowed

    async def fetch_page_content(self, url: str, source_url_for_referrer: Optional[str] = None) -> Optional[Tuple[bytes, str]]:
        """Fetches URL content, handling errors, rate limiting, proxies, UA rotation, and referrers."""
        limiter = await self._get_domain_limiter(url)
        await limiter.acquire()
        
        current_ua = self._get_random_user_agent()
        headers = {"User-Agent": current_ua}
        if source_url_for_referrer:
            headers["Referer"] = source_url_for_referrer
            logger.debug(f"Using Referer: {source_url_for_referrer} for request to {url}")

        current_proxy_str = self._get_current_proxy()
        request_proxies = {"http://": current_proxy_str, "https://": current_proxy_str} if current_proxy_str else None
        
        client_to_use = self.http_client_no_proxy # Use the base client, and pass proxies to the request method

        try:
            log_proxy_msg = f"(Proxy: {current_proxy_str})" if current_proxy_str else "(No Proxy)"
            logger.debug(f"Fetching URL: {url} {log_proxy_msg} (UA: {current_ua})")
            
            response = await client_to_use.get(url, headers=headers, proxies=request_proxies) # type: ignore
            response.raise_for_status() 
            content_type = response.headers.get("content-type", "").lower()
            content_bytes = await response.aread() # Read all bytes after status check
            logger.debug(f"Fetched {url}, Status: {response.status_code}, CT: {content_type}, Size: {len(content_bytes)}B")
            return content_bytes, content_type
        except httpx.ProxyError as e:
            logger.warning(f"Proxy error {current_proxy_str} fetching {url}: {type(e).__name__} - {e}. Trying without proxy if this was the first attempt with proxy.")
            # Potentially retry without proxy or with a different proxy here
            # For now, just log and fail this attempt
        except httpx.TimeoutException: logger.warning(f"Timeout fetching {url}")
        except httpx.ConnectError: logger.warning(f"Connection error fetching {url}")
        except httpx.ReadError: logger.warning(f"Read error fetching {url}")
        except httpx.HTTPStatusError as e:
            # Common non-fatal errors
            if e.response.status_code in [404, 410]: logger.info(f"HTTP {e.response.status_code} for {url}") 
            elif e.response.status_code in [403, 401]: logger.warning(f"HTTP {e.response.status_code} (Forbidden/Unauthorized) for {url}")
            elif e.response.status_code == 429: logger.warning(f"HTTP 429 (Too Many Requests) for {url}. Consider increasing delay or using better proxies.")
            else: logger.warning(f"HTTP status error {e.response.status_code} fetching {url}: {e.response.reason_phrase}")
        except httpx.RequestError as e: logger.warning(f"HTTP request error fetching {url}: {type(e).__name__} - {e}")
        except Exception as e: logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
        finally: await limiter.release()
        return None

    async def _extract_sitemap_urls_from_html(self, html_content: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        sitemap_urls: Set[str] = set() # Use set for automatic deduplication
        for link_tag in soup.find_all('link', attrs={'rel': 'sitemap'}):
            href = link_tag.get('href')
            if href: sitemap_urls.add(urljoin(base_url, href))
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href and ('sitemap.xml' in href or 'sitemap_index.xml' in href or 'sitemap.txt' in href):
                 sitemap_urls.add(urljoin(base_url, href))

        if not sitemap_urls: # Guess common paths if none found explicitly
            parsed_base = urlparse(base_url)
            domain_base = f"{parsed_base.scheme}://{parsed_base.netloc}"
            common_paths = ["/sitemap.xml", "/sitemap_index.xml", "/sitemap.txt", "/sitemap.xml.gz"]
            for path in common_paths: sitemap_urls.add(urljoin(domain_base, path))
        
        unique_sitemap_urls_list = list(sitemap_urls)
        if unique_sitemap_urls_list:
            logger.info(f"Found {len(unique_sitemap_urls_list)} potential sitemap URLs on {base_url}")
        return unique_sitemap_urls_list

    async def _fetch_and_parse_sitemap(self, sitemap_url: str, source_of_sitemap_url: Optional[str]=None) -> AsyncGenerator[str, None]:
        if sitemap_url in self.processed_sitemap_urls or await self._check_if_stopped(): return
        self.processed_sitemap_urls.add(sitemap_url)

        logger.info(f"Fetching sitemap: {sitemap_url}")
        sitemap_content_tuple = await self.fetch_page_content(sitemap_url, source_url_for_referrer=source_of_sitemap_url)
        if not sitemap_content_tuple: return

        sitemap_bytes, sitemap_content_type = sitemap_content_tuple
        
        # Handle Gzipped sitemaps
        if sitemap_url.endswith(".gz") or "gzip" in sitemap_content_type:
            try:
                import gzip
                sitemap_bytes = gzip.decompress(sitemap_bytes)
                sitemap_content_type = "application/xml" if sitemap_url.endswith(".xml.gz") else "text/plain" # Assume type after decompress
                logger.info(f"Decompressed gzipped sitemap: {sitemap_url}")
            except Exception as e:
                logger.error(f"Failed to decompress gzipped sitemap {sitemap_url}: {e}")
                return

        if "text/plain" in sitemap_content_type:
            try:
                sitemap_text = sitemap_bytes.decode('utf-8', errors='replace')
                for line in sitemap_text.splitlines():
                    url = line.strip()
                    if url and (url.startswith("http://") or url.startswith("https://")): yield url
            except Exception as e: logger.error(f"Error decoding/parsing TXT sitemap {sitemap_url}: {e}")
            return

        if "xml" in sitemap_content_type:
            try:
                sitemap_text = sitemap_bytes.decode('utf-8', errors='replace')
                root = ET.fromstring(sitemap_text)
                namespace_match = re.match(r'\{([^}]+)\}', root.tag)
                namespace = namespace_match.group(0) if namespace_match else ''

                if root.tag == f'{namespace}sitemapindex':
                    logger.info(f"Processing sitemap index: {sitemap_url}")
                    sub_sitemap_tasks = []
                    for sitemap_element in root.findall(f'{namespace}sitemap/{namespace}loc'):
                        sub_sitemap_url = sitemap_element.text.strip() if sitemap_element.text else None
                        if sub_sitemap_url and sub_sitemap_url not in self.processed_sitemap_urls:
                            sub_sitemap_tasks.append(self._fetch_and_parse_sitemap(sub_sitemap_url, source_of_sitemap_url=sitemap_url)) # Pass current sitemap as referrer
                    
                    for task_gen in asyncio.as_completed(sub_sitemap_tasks): # Process sub-sitemaps concurrently
                        async for url_from_sub in await task_gen: yield url_from_sub

                elif root.tag == f'{namespace}urlset':
                    logger.info(f"Processing URL set sitemap: {sitemap_url}")
                    for url_element in root.findall(f'{namespace}url/{namespace}loc'):
                        url = url_element.text.strip() if url_element.text else None
                        if url: yield unquote(url) # Unquote URLs from sitemaps
                else: logger.warning(f"Unknown root tag '{root.tag}' in XML sitemap: {sitemap_url}")
            except ET.ParseError as e: logger.error(f"XML parsing error for sitemap {sitemap_url}: {e}", exc_info=False)
            except Exception as e: logger.error(f"Error processing XML sitemap {sitemap_url}: {e}", exc_info=True)
        else: logger.debug(f"Skipping sitemap {sitemap_url}, CT: {sitemap_content_type}")


    async def process_url(self, url: str, current_depth: int, source_of_url: Optional[str] = None) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        if await self._check_if_stopped():
            logger.info(f"Stopping URL processing for {url} (depth {current_depth}) due to stop signal.")
            return

        try:
             parsed_url_obj = urlparse(url)
             normalized_url = parsed_url_obj._replace(fragment="", query="").geturl() # More aggressive normalization
        except ValueError:
             logger.warning(f"Failed to parse/normalize URL: {url}. Skipping.")
             return

        if normalized_url in self.visited_urls:
            # logger.debug(f"URL already visited: {normalized_url}, skipping.")
            return
        self.visited_urls.add(normalized_url)

        if current_depth > self.settings.crawl_depth:
            logger.debug(f"Max depth {self.settings.crawl_depth} reached for {url}")
            return
        
        # Determine user agent for this specific request for robots.txt check
        # This UA should ideally be the one used for actual fetching later.
        ua_for_this_request = self._get_random_user_agent() 
        if not await self.is_allowed_by_robots(url, ua_for_this_request): # Pass UA
             logger.info(f"Skipping {url} due to robots.txt disallow rule for UA {ua_for_this_request}.")
             return

        logger.info(f"Processing URL: {url} (Depth: {current_depth}, From: {source_of_url or 'Initial'})")
        content_data_tuple = await self.fetch_page_content(url, source_url_for_referrer=source_of_url)

        if not content_data_tuple: return 

        raw_content_bytes, content_type_header = content_data_tuple
        file_meta = file_identifier.identify_file_type_and_name(url, content_type_header, raw_content_bytes[:2048]) # Increase bytes for magic
        target_extensions_set = {ext.lstrip('.').lower() for ext in self.settings.file_extensions}
        is_target_file_extension = file_meta.extension.lower() in target_extensions_set

        if is_target_file_extension:
            logger.info(f"Target file type '{file_meta.extension}' identified: {url}")
            keywords_in_filename = keyword_matcher.match_keywords_in_text(file_meta.name, self.settings.keywords)
            
            # For text-based files, attempt to decode and check content
            keywords_in_content = set()
            is_text_based = any(file_meta.extension.lower() in ext_list for ext_list in [FILE_TYPE_EXTENSIONS.text, FILE_TYPE_EXTENSIONS.json, FILE_TYPE_EXTENSIONS.code, FILE_TYPE_EXTENSIONS.config])
            
            if is_text_based and len(raw_content_bytes) < (2 * 1024 * 1024): # Limit content check to 2MB files
                try:
                    # Try common encodings
                    decoded_content = ""
                    try: decoded_content = raw_content_bytes.decode('utf-8')
                    except UnicodeDecodeError:
                        try: decoded_content = raw_content_bytes.decode('latin-1')
                        except UnicodeDecodeError: logger.warning(f"Could not decode content for keyword check: {url}")
                    
                    if decoded_content:
                        keywords_in_content = keyword_matcher.match_keywords_in_text(decoded_content[:50000], self.settings.keywords) # Check first 50KB
                        if keywords_in_content: logger.info(f"Keywords {keywords_in_content} found in content of {url}")
                except Exception as e_content_check: logger.error(f"Error checking content keywords for {url}: {e_content_check}")

            all_found_keywords = keywords_in_filename.union(keywords_in_content)

            if all_found_keywords:
                logger.info(f"Keywords {all_found_keywords} found in filename/metadata/content for: {url}. Proceeding to download/record.")
                try:
                    download_result_schema = await downloader.download_and_store_file(
                        self.http_client_no_proxy, # Use base client for download, proxy for discovery
                        url, file_meta, self.job_id, list(all_found_keywords),
                        raw_content_bytes if len(raw_content_bytes) < (5 * 1024 * 1024) else None,
                        proxies=None # Downloads typically don't need discovery proxy
                    )
                    if download_result_schema:
                        try:
                            db_downloaded_file = crud.create_downloaded_file(db=self.db, downloaded_file=download_result_schema)
                            logger.info(f"Recorded downloaded file in DB: {db_downloaded_file.id} from {url}")
                            yield db_downloaded_file
                        except SQLAlchemyError as db_err: logger.error(f"DB error recording file from {url}: {db_err}", exc_info=True)
                        except Exception as db_e: logger.error(f"Unexpected error recording file from {url}: {db_e}", exc_info=True)
                except Exception as e: logger.error(f"Download/storage process failed for {url}: {e}", exc_info=True)

        if "text/html" in content_type_header:
            if await self._check_if_stopped(): return
            try: html_content_str = raw_content_bytes.decode('utf-8', errors='replace')
            except Exception as decode_err: logger.error(f"Failed to decode HTML content from {url}: {decode_err}"); return

            sitemap_urls_on_page = await self._extract_sitemap_urls_from_html(html_content_str, url)
            sitemap_processing_tasks = []
            for sitemap_url_found in sitemap_urls_on_page:
                if sitemap_url_found not in self.processed_sitemap_urls and sitemap_url_found not in self.visited_urls:
                     sitemap_processing_tasks.append(self._process_sitemap_and_its_urls(sitemap_url_found, current_depth +1, source_of_sitemap_url=url))

            if sitemap_processing_tasks:
                logger.info(f"Found {len(sitemap_processing_tasks)} new sitemaps from {url}.")
                for task_gen in asyncio.as_completed(sitemap_processing_tasks):
                    if await self._check_if_stopped(): break
                    try:
                        async for found_file_schema_from_sitemap in await task_gen: yield found_file_schema_from_sitemap
                    except Exception as e_sitemap_proc: logger.error(f"Error processing URLs from sitemap gen (origin {url}): {e_sitemap_proc}", exc_info=True)

            if current_depth < self.settings.crawl_depth:
                try:
                    links_on_page = recursive.extract_links_from_html(html_content_str, url)
                    sub_tasks = []
                    for link_url in links_on_page:
                        if await self._check_if_stopped(): break
                        if link_url not in self.visited_urls:
                           sub_tasks.append(self.process_url(link_url, current_depth + 1, source_of_url=url)) # Pass current URL as source
                    if await self._check_if_stopped(): return
                    for completed_task_gen in asyncio.as_completed(sub_tasks):
                        if await self._check_if_stopped(): break
                        try:
                            async for found_file_schema in await completed_task_gen: yield found_file_schema
                        except Exception as e_inner: logger.error(f"Error processing sub-link gen from {url}: {e_inner}", exc_info=True)
                except Exception as parse_err: logger.error(f"Error parsing HTML/links from {url}: {parse_err}", exc_info=True)
    
    async def _process_sitemap_and_its_urls(self, sitemap_url: str, depth_for_sitemap_content: int, source_of_sitemap_url: Optional[str] = None) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        if await self._check_if_stopped(): return
        
        self.visited_urls.add(urlparse(sitemap_url)._replace(fragment="", query="").geturl()) # Mark sitemap URL itself as visited

        url_processing_tasks = []
        async for url_from_sitemap in self._fetch_and_parse_sitemap(sitemap_url, source_of_sitemap_url=source_of_sitemap_url):
            if await self._check_if_stopped(): break
            if url_from_sitemap not in self.visited_urls:
                 # URLs from sitemap are processed at the depth they were discovered (depth of page linking to sitemap + 1, or 0 if sitemap is seed)
                 url_processing_tasks.append(self.process_url(url_from_sitemap, depth_for_sitemap_content, source_of_url=sitemap_url))
        
        if url_processing_tasks:
            logger.info(f"Processing {len(url_processing_tasks)} URLs from sitemap {sitemap_url}")
            for task_gen in asyncio.as_completed(url_processing_tasks):
                if await self._check_if_stopped(): break
                try:
                    async for file_schema in await task_gen: yield file_schema
                except Exception as e_sitemap_url_proc: logger.error(f"Error processing URL from sitemap {sitemap_url}: {e_sitemap_url_proc}", exc_info=True)


    async def start_crawling(self) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        start_time = time.monotonic()
        files_found_count = 0
        if await self._check_if_stopped():
            logger.info(f"Crawl job {self.job_id} is already stopping/stopped. Not starting.")
            if self.http_client_no_proxy and not self.http_client_no_proxy.is_closed: await self.http_client_no_proxy.aclose()
            return

        try:
            crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="running", last_run_at=datetime.now(timezone.utc))
            self.db.commit() # Commit status early
            logger.info(f"Starting deep crawl for job {self.job_id}")
            initial_urls_to_process: Set[str] = set()

            for seed_url_str in self.settings.seed_urls:
                if await self._check_if_stopped(): break
                try:
                    parsed = urlparse(seed_url_str); normalized = parsed._replace(fragment="", query="").geturl()
                    if parsed.scheme in ['http', 'https'] and parsed.netloc and normalized not in self.visited_urls: initial_urls_to_process.add(normalized)
                    else: logger.warning(f"Skipping invalid or duplicate seed URL: {seed_url_str}")
                except ValueError: logger.warning(f"Skipping invalid seed URL format: {seed_url_str}")
            
            if await self._check_if_stopped(): raise asyncio.CancelledError("Job stopped during seed URL processing")

            if self.settings.use_search_engines and self.settings.search_dorks:
                logger.info(f"Executing {len(self.settings.search_dorks)} search dorks...")
                search_client = await self._get_http_client_with_proxy() # Use a (potentially proxied) client for dorks
                
                dork_tasks = [
                    search_engine_driver.execute_dork(
                        dork, search_client, max_results=self.settings.max_results_per_dork or 20
                    ) for dork in self.settings.search_dorks if not await self._check_if_stopped()
                ]
                if not await self._check_if_stopped() and dork_tasks:
                    dork_results_list_of_lists = await asyncio.gather(*[self._collect_async_gen(gen) for gen in dork_tasks], return_exceptions=True)
                    for i, result_or_exc in enumerate(dork_results_list_of_lists):
                         if await self._check_if_stopped(): break
                         dork_query = self.settings.search_dorks[i]
                         if isinstance(result_or_exc, Exception): logger.error(f"Error executing dork '{dork_query}': {result_or_exc}"); continue
                         added_count = 0
                         for dork_url in result_or_exc:
                             try:
                                 parsed = urlparse(dork_url); normalized = parsed._replace(fragment="", query="").geturl()
                                 if parsed.scheme in ['http', 'https'] and parsed.netloc and normalized not in self.visited_urls and normalized not in initial_urls_to_process:
                                      initial_urls_to_process.add(normalized); added_count += 1
                             except ValueError: logger.warning(f"Skipping invalid URL from dork '{dork_query}': {dork_url}")
                         logger.info(f"Dork '{dork_query}' added {added_count} new URLs.")
                if search_client != self.http_client_no_proxy and not search_client.is_closed: # Close if it was a temp proxied client
                    await search_client.aclose()


            if await self._check_if_stopped(): raise asyncio.CancelledError("Job stopped during dork processing")

            if not initial_urls_to_process: logger.warning(f"No initial URLs found for job {self.job_id}. Crawl will stop.")
            else: self.initial_urls_found = True; logger.info(f"Total unique initial URLs to process: {len(initial_urls_to_process)}")

            if initial_urls_to_process:
                processing_tasks = [self.process_url(url, 0, source_of_url=None) for url in initial_urls_to_process] # No source for initial URLs
                for task_gen_completed in asyncio.as_completed(processing_tasks):
                    if await self._check_if_stopped(): break
                    try:
                        async for file_schema in await task_gen_completed:
                             if await self._check_if_stopped(): break
                             files_found_count += 1; yield file_schema
                    except asyncio.CancelledError: logger.info(f"A processing task for job {self.job_id} was cancelled."); break
                    except Exception as task_err: logger.error(f"Error in a main URL processing task for job {self.job_id}: {task_err}", exc_info=True)

        except asyncio.CancelledError: logger.info(f"Crawl job {self.job_id} was cancelled/stopped.")
        except Exception as e:
            logger.error(f"Critical error during crawl job {self.job_id}: {e}", exc_info=True)
            try: crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="failed"); self.db.commit()
            except Exception as db_e: logger.error(f"Failed to update job status to 'failed' for {self.job_id} after critical error: {db_e}"); self.db.rollback()
        finally:
            final_status_to_set = "unknown"
            try:
                # Re-fetch current status from DB before deciding final status
                current_db_status_obj = crud.get_crawl_job_status_only(self.db, self.job_id) # Fetch fresh status

                if current_db_status_obj == "running": # Only update if it was still 'running'
                    if self._should_stop_event.is_set(): # If stopped by signal
                        final_status_to_set = "failed" # Or "stopped" if you add such a status
                    elif files_found_count > 0: final_status_to_set = "completed"
                    elif self.initial_urls_found: final_status_to_set = "completed_empty" # Found URLs but no matching files
                    else: final_status_to_set = "completed_empty" # Found no initial URLs
                    
                    crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status=final_status_to_set)
                    self.db.commit()
                    logger.info(f"Crawl job {self.job_id} finished. Final status: {final_status_to_set}. Files yielded: {files_found_count}")
                elif current_db_status_obj == "stopping": # If it was already set to 'stopping' by API
                     final_status_to_set = "failed" # Mark as failed as it didn't complete normally
                     crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status=final_status_to_set)
                     self.db.commit()
                     logger.info(f"Crawl job {self.job_id} was externally stopped and marked as 'failed'.")
                else: # Job status was already something else (e.g. failed, completed by API call race)
                    logger.info(f"Job {self.job_id} status was '{current_db_status_obj}' (not 'running' or 'stopping'). Not overriding final status from crawl completion logic.")
                    final_status_to_set = current_db_status_obj # Keep the existing status
            
            except Exception as final_status_err: 
                logger.error(f"Error during final status update/check for job {self.job_id}: {final_status_err}", exc_info=True)
                if self.db.is_active: self.db.rollback()


            if self.http_client_no_proxy and not self.http_client_no_proxy.is_closed:
                await self.http_client_no_proxy.aclose()
                logger.info(f"Base HTTP client closed for job {self.job_id}.")
            end_time = time.monotonic()
            logger.info(f"Total execution time for job {self.job_id}: {end_time - start_time:.2f} seconds. Final resolved status: {final_status_to_set}")

    async def _collect_async_gen(self, agen: AsyncGenerator[str, None]) -> List[str]:
        items = []
        try:
            async for item in agen:
                if await self._check_if_stopped(): break
                items.append(item)
        except Exception as e: logger.error(f"Error collecting from an async generator: {e}", exc_info=True)
        return items


# For identify_file_type_and_name to access easily
FILE_TYPE_EXTENSIONS = {
  "text": ["txt", "log", "csv", "md", "rtf", "tsv", "ini", "conf", "cfg", "pem", "key"],
  "json": ["json", "jsonl", "geojson"],
  "database": ["sql", "db", "sqlite", "sqlite3", "mdb", "accdb", "dump"],
  "archive": ["zip", "tar", "gz", "bz2", "7z", "rar", "tgz"],
  "code": ["py", "js", "java", "c", "cpp", "cs", "php", "rb", "go", "html", "css", "sh", "ps1", "bat", "xml", "yaml", "yml"],
  "spreadsheet": ["xls", "xlsx", "ods"],
  "document": ["doc", "docx", "odt", "pdf", "ppt", "pptx", "odp"],
  "config": ["config", "conf", "cfg", "ini", "xml", "yaml", "yml", "env", "pem", "key", "crt"],
  # Add more categories and extensions as needed
}

    