
import logging
import asyncio
import httpx # Modern async HTTP client, preferred over requests for async code
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional, Tuple, Dict, AsyncGenerator
from datetime import datetime, timezone
import re
import time
import random
import uuid

from breachwatch.api.v1 import schemas # For type hinting if needed for settings
from breachwatch.utils.config_loader import get_settings
from breachwatch.core import file_identifier, keyword_matcher, downloader
from breachwatch.strategies import search_engine_driver, direct_probe, recursive
from breachwatch.storage import crud # For saving results
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)
config_settings = get_settings()

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
                await asyncio.sleep(wait_time) # Sleep outside the lock if possible, but complex with condition

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
    Orchestrates the crawling process using various strategies.
    Manages visited URLs, depth, and delegates to specific crawlers.
    Includes robust error handling and graceful shutdown mechanisms.
    """
    def __init__(self, job_id: uuid.UUID, crawl_settings: schemas.CrawlSettingsSchema, db: Session):
        self.job_id = job_id
        self.settings = crawl_settings
        self.db = db
        self.visited_urls: Set[str] = set()
        self.domain_limiters: Dict[str, DomainLimiter] = {}
        self.user_agent = self.settings.custom_user_agent or config_settings.DEFAULT_USER_AGENT # Use custom if provided
        self.request_timeout = config_settings.REQUEST_TIMEOUT
        self._should_stop_event = asyncio.Event() # Event to signal graceful shutdown
        self.initial_urls_found = False # Track if any URLs were found from seeds/dorks initially


        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100) # General client limits
        self.http_client = httpx.AsyncClient(
            headers={"User-Agent": self.user_agent},
            timeout=self.request_timeout,
            follow_redirects=True,
            limits=limits,
            verify=False # Consider adding SSL verification control if needed config_settings.VERIFY_SSL?
        )
        logger.info(f"MasterCrawler for job {self.job_id} initialized. User Agent: {self.user_agent}")
        logger.info(f"Keywords: {self.settings.keywords[:5]}..., Extensions: {self.settings.file_extensions[:5]}...")
        logger.info(f"Crawl Depth: {self.settings.crawl_depth}, Dorks: {len(self.settings.search_dorks)}")
        logger.info(f"Request Delay: {self.settings.request_delay_seconds}s, Max Concurrent per Domain: {self.settings.max_concurrent_requests_per_domain}")
        logger.info(f"Respect robots.txt: {self.settings.respect_robots_txt}") # TODO: Implement robots.txt check

    async def _check_if_stopped(self) -> bool:
        """Checks if the stop signal has been received or job status is 'stopping'."""
        if self._should_stop_event.is_set():
            return True

        # Reduced frequency DB check for external stop requests
        # Check roughly every 10 seconds, or based on loop iteration count if preferred
        # Avoid checking on every single URL processing.
        if random.randint(1, 100) > 98: # Roughly 2% chance per check
            try:
                # Use with_for_update to avoid potential race conditions if needed, but likely overkill here
                job = self.db.query(models.CrawlJob.status).filter(models.CrawlJob.id == self.job_id).scalar() # Fetch only status
                if job == "stopping":
                    self._should_stop_event.set()
                    logger.info(f"Job {self.job_id} stop signal received via DB status 'stopping'.")
                    return True
            except SQLAlchemyError as db_err:
                 logger.error(f"Database error checking job status for {self.job_id}: {db_err}", exc_info=True)
            except Exception as e:
                 logger.error(f"Unexpected error checking job status for {self.job_id}: {e}", exc_info=True)

        return False

    async def stop_crawler(self):
        """Signals the crawler to stop gracefully."""
        if not self._should_stop_event.is_set():
            logger.info(f"MasterCrawler for job {self.job_id} received stop signal.")
            self._should_stop_event.set()
            try:
                # Update status in DB to 'stopping' so it's visible externally
                crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="stopping")
            except Exception as e:
                 logger.error(f"Failed to update job {self.job_id} status to 'stopping' in DB after signal: {e}")


    async def _get_domain_limiter(self, url: str) -> DomainLimiter:
        try:
            domain = urlparse(url).netloc
            if not domain:
                logger.warning(f"Could not parse domain from URL: {url}. Using default limiter.")
                # Use a common limiter for invalid/non-HTTP URLs to prevent overwhelming it
                domain = "__no_domain__"
        except ValueError:
             logger.warning(f"ValueError parsing domain from URL: {url}. Using default limiter.")
             domain = "__parse_error__"

        if domain not in self.domain_limiters:
            # Create limiter with potentially domain-specific settings if needed in future
            self.domain_limiters[domain] = DomainLimiter(
                delay_seconds=self.settings.request_delay_seconds,
                max_concurrent=self.settings.max_concurrent_requests_per_domain or 2
            )
        return self.domain_limiters[domain]

    async def fetch_page_content(self, url: str) -> Optional[Tuple[bytes, str]]:
        """Fetches URL content, handling errors and rate limiting."""
        limiter = await self._get_domain_limiter(url)
        await limiter.acquire()
        try:
            logger.debug(f"Fetching URL: {url}")
            response = await self.http_client.get(url) # timeout is set on client
            response.raise_for_status() # Raise HTTPStatusError for 4xx/5xx responses

            content_type = response.headers.get("content-type", "").lower()
            # Read content carefully, maybe limit size for initial check?
            # For now, read the whole thing if status is OK.
            content_bytes = await response.aread()

            logger.debug(f"Fetched {url}, Status: {response.status_code}, Content-Type: {content_type}, Size: {len(content_bytes)} bytes")
            return content_bytes, content_type

        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return None
        except httpx.ConnectError:
             logger.warning(f"Connection error fetching {url}")
             return None
        except httpx.ReadError:
             logger.warning(f"Read error fetching {url}")
             return None
        except httpx.HTTPStatusError as e:
            # Log specific status errors - 404 is common and less severe than 5xx
            if e.response.status_code == 404:
                logger.info(f"HTTP 404 Not Found for {url}")
            elif e.response.status_code == 403:
                 logger.warning(f"HTTP 403 Forbidden for {url}")
            else:
                 logger.warning(f"HTTP status error {e.response.status_code} fetching {url}: {e.response.reason_phrase}")
            return None
        except httpx.RequestError as e: # Catch other httpx request errors
            logger.warning(f"HTTP request error fetching {url}: {type(e).__name__} - {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
            return None
        finally:
            await limiter.release()

    async def process_url(self, url: str, current_depth: int) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """Processes a single URL: fetches, identifies, downloads (if matches), and finds links."""
        if await self._check_if_stopped():
            logger.info(f"Stopping URL processing for {url} at depth {current_depth} due to stop signal.")
            return

        # Use urlparse to normalize URL slightly (e.g., remove fragment) before adding to visited
        try:
             parsed_url = urlparse(url)
             normalized_url = parsed_url._replace(fragment="").geturl()
        except ValueError:
             logger.warning(f"Failed to parse/normalize URL: {url}. Skipping.")
             return

        if normalized_url in self.visited_urls:
            logger.debug(f"URL already visited: {normalized_url}, skipping.")
            return
        self.visited_urls.add(normalized_url)

        if current_depth > self.settings.crawl_depth:
            logger.debug(f"Max depth {self.settings.crawl_depth} reached for {url}")
            return

        # TODO: Implement robots.txt checking if self.settings.respect_robots_txt is True
        # Before fetching, check if crawling this URL is allowed by robots.txt
        # Requires fetching and parsing robots.txt for the domain. Libraries like 'reppy' can help.
        # if self.settings.respect_robots_txt and not await self.is_allowed_by_robots(url):
        #      logger.info(f"Skipping {url} due to robots.txt disallow rule.")
        #      return


        logger.info(f"Processing URL: {url} at depth {current_depth}")
        content_data_tuple = await self.fetch_page_content(url)

        if not content_data_tuple:
            return # Fetch failed or returned error

        raw_content_bytes, content_type_header = content_data_tuple
        file_meta = file_identifier.identify_file_type_and_name(url, content_type_header, raw_content_bytes[:1024])
        target_extensions_set = {ext.lstrip('.').lower() for ext in self.settings.file_extensions}
        is_target_file_extension = file_meta.extension.lower() in target_extensions_set

        if is_target_file_extension:
            logger.info(f"Target file type '{file_meta.extension}' identified: {url}")
            # Decision: Do we download first, then check keywords, or check filename first?
            # Check filename/metadata first is lighter. Check content requires download.
            keywords_in_filename_or_metadata = keyword_matcher.match_keywords_in_text(file_meta.name, self.settings.keywords)

            # Add logic here: maybe download *all* target extensions, or only if keyword match in name?
            # For now, require keyword match in name/metadata OR proceed to download and check content
            should_download = False
            if keywords_in_filename_or_metadata:
                 logger.info(f"Keywords {keywords_in_filename_or_metadata} found in filename/metadata for: {url}. Proceeding to download.")
                 should_download = True
            # --- Add content keyword check logic if desired ---
            # else if file_meta.mime_type and file_meta.mime_type.startswith('text/'): # Or other checkable types
            #      logger.debug(f"Checking content of text file {url} for keywords...")
            #      # Decode carefully
            #      try:
            #          text_content = raw_content_bytes.decode('utf-8', errors='ignore')
            #          keywords_in_content = keyword_matcher.match_keywords_in_text(text_content, self.settings.keywords)
            #          if keywords_in_content:
            #              logger.info(f"Keywords {keywords_in_content} found in content of: {url}. Proceeding to download.")
            #              should_download = True
            #              keywords_found_triggering_download = keywords_in_content # Store these keywords
            #          else:
            #               logger.debug(f"No keywords found in content of {url}")
            #      except Exception as decode_err:
            #          logger.warning(f"Could not decode/check content of {url}: {decode_err}")
            # -----------------------------------------------------

            if should_download:
                try:
                    # Pass found keywords (could be from filename or content)
                    keywords_for_record = list(keywords_in_filename_or_metadata) # or keywords_in_content if implemented

                    download_result_schema = await downloader.download_and_store_file(
                        self.http_client,
                        url,
                        file_meta,
                        self.job_id,
                        keywords_for_record,
                        # Pass existing bytes if small enough and already read, avoids re-fetch
                        raw_content_bytes if len(raw_content_bytes) < (5 * 1024 * 1024) else None
                    )
                    if download_result_schema:
                        # Save to database
                        try:
                            db_downloaded_file = crud.create_downloaded_file(db=self.db, downloaded_file=download_result_schema)
                            logger.info(f"Recorded downloaded file in DB: {db_downloaded_file.id} from {url}")
                            yield db_downloaded_file
                        except SQLAlchemyError as db_err:
                             logger.error(f"Database error recording downloaded file from {url}: {db_err}", exc_info=True)
                        except Exception as db_e:
                             logger.error(f"Unexpected error recording downloaded file from {url}: {db_e}", exc_info=True)

                except Exception as e:
                    logger.error(f"Failed during download/storage process for {url}: {e}", exc_info=True)
                    # Decide if this should mark the job as failed? For now, just log.

        # If it's an HTML page and we haven't reached max depth, extract and queue links
        if "text/html" in content_type_header and current_depth < self.settings.crawl_depth:
            if await self._check_if_stopped():
                logger.info(f"Stopping HTML processing for {url} due to stop signal.")
                return

            try:
                html_content_str = raw_content_bytes.decode('utf-8', errors='replace')
            except UnicodeDecodeError:
                 logger.warning(f"Could not decode HTML content from {url} as UTF-8. Attempting fallback.")
                 try:
                     # Try common fallbacks
                     html_content_str = raw_content_bytes.decode('latin-1', errors='replace')
                 except Exception as fallback_decode_err:
                      logger.error(f"Failed to decode HTML content from {url} with UTF-8 and fallbacks: {fallback_decode_err}")
                      return # Cannot process links if decoding fails

            try:
                links_on_page = recursive.extract_links_from_html(html_content_str, url)
                logger.debug(f"Found {len(links_on_page)} links on {url} to process for depth {current_depth + 1}.")

                sub_tasks = []
                for link_url in links_on_page:
                    if await self._check_if_stopped(): break
                    # Avoid queueing links already visited or exceeding depth implicitly
                    if link_url not in self.visited_urls:
                       sub_tasks.append(self.process_url(link_url, current_depth + 1))

                if await self._check_if_stopped(): return

                # Process sub-tasks concurrently using asyncio.gather or as_completed
                # Using as_completed to yield results as they become available
                for completed_task_gen in asyncio.as_completed(sub_tasks):
                    if await self._check_if_stopped(): break
                    try:
                        async for found_file_schema in await completed_task_gen:
                            if await self._check_if_stopped(): break
                            yield found_file_schema
                    except Exception as e_inner:
                        # Log error in sub-task but continue processing others
                        logger.error(f"Error processing a sub-link generator originating from {url}: {e_inner}", exc_info=True)

            except Exception as parse_err:
                 logger.error(f"Error parsing HTML or processing links from {url}: {parse_err}", exc_info=True)


    async def _run_sub_task(self, coro):
        """Wrapper to run a sub-task and handle potential errors."""
        try:
            return await coro
        except Exception as e:
            logger.error(f"Error in sub-task execution: {e}", exc_info=True)
            return [] # Return empty list or None on error

    async def start_crawling(self) -> AsyncGenerator[schemas.DownloadedFileSchema, None]:
        """Main entry point to start the crawl job."""
        start_time = time.monotonic()
        files_found_count = 0
        if await self._check_if_stopped():
            logger.info(f"Crawl job {self.job_id} is already stopping/stopped. Not starting.")
            await self.http_client.aclose()
            return

        try:
            crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="running", last_run_at=datetime.now(timezone.utc))
            logger.info(f"Starting deep crawl for job {self.job_id}")

            initial_urls_to_process: Set[str] = set()

            # 1. Add Seed URLs
            for seed_url_str in self.settings.seed_urls:
                if await self._check_if_stopped(): break
                try:
                    # Basic validation/normalization
                    parsed = urlparse(seed_url_str)
                    if parsed.scheme in ['http', 'https'] and parsed.netloc:
                         normalized = parsed._replace(fragment="").geturl()
                         if normalized not in self.visited_urls:
                              initial_urls_to_process.add(normalized)
                    else:
                         logger.warning(f"Skipping invalid seed URL: {seed_url_str}")
                except ValueError:
                     logger.warning(f"Skipping invalid seed URL format: {seed_url_str}")
            logger.info(f"Collected {len(initial_urls_to_process)} unique, valid seed URLs.")

            if await self._check_if_stopped(): raise asyncio.CancelledError("Job stopped during seed URL processing")

            # 2. Execute Search Dorks (if enabled)
            if self.settings.use_search_engines and self.settings.search_dorks:
                logger.info(f"Executing {len(self.settings.search_dorks)} search dorks...")
                dork_tasks = []
                for dork in self.settings.search_dorks:
                    if await self._check_if_stopped(): break
                    dork_tasks.append(
                        search_engine_driver.execute_dork(
                            dork,
                            self.http_client,
                            max_results=self.settings.max_results_per_dork or 20
                        )
                    )

                if not await self._check_if_stopped():
                    # Gather results from all dork generators concurrently
                    # Handle potential errors from individual dork executions
                    dork_results_generators = await asyncio.gather(*[self._collect_async_gen(gen) for gen in dork_tasks], return_exceptions=True)

                    urls_from_dorks = 0
                    for i, result_or_exc in enumerate(dork_results_generators):
                         dork_query = self.settings.search_dorks[i]
                         if isinstance(result_or_exc, Exception):
                             logger.error(f"Error executing dork '{dork_query}': {result_or_exc}")
                             continue # Skip this dork's results

                         # result_or_exc is List[str] here
                         added_count = 0
                         for dork_url in result_or_exc:
                             try:
                                 parsed = urlparse(dork_url)
                                 if parsed.scheme in ['http', 'https'] and parsed.netloc:
                                      normalized = parsed._replace(fragment="").geturl()
                                      if normalized not in self.visited_urls and normalized not in initial_urls_to_process:
                                           initial_urls_to_process.add(normalized)
                                           added_count += 1
                             except ValueError:
                                  logger.warning(f"Skipping invalid URL from dork '{dork_query}': {dork_url}")
                         urls_from_dorks += added_count
                         logger.info(f"Dork '{dork_query}' added {added_count} new URLs to process queue (Total found: {len(result_or_exc)}).")
                    logger.info(f"Added {urls_from_dorks} unique URLs from dork results.")


            if await self._check_if_stopped(): raise asyncio.CancelledError("Job stopped during dork processing")

            if not initial_urls_to_process:
                logger.warning(f"No initial URLs found from seeds or dorks for job {self.job_id}. Crawl will stop.")
                # No need to update status here, final block handles it based on initial_urls_found
            else:
                 self.initial_urls_found = True # Mark that we found starting points

            logger.info(f"Total unique initial URLs to process: {len(initial_urls_to_process)}")

            # 3. Process Initial URLs and Recursively Crawl
            if initial_urls_to_process:
                # Use a queue or manage tasks directly
                processing_tasks = [self.process_url(url, 0) for url in initial_urls_to_process]

                # Process results as they complete
                for task_gen in asyncio.as_completed(processing_tasks):
                    if await self._check_if_stopped(): break
                    try:
                        async for file_schema in await task_gen:
                             if await self._check_if_stopped(): break
                             files_found_count += 1
                             yield file_schema
                    except asyncio.CancelledError:
                        logger.info(f"A processing task for job {self.job_id} was cancelled.")
                        break # Exit loop if cancelled
                    except Exception as task_err:
                        logger.error(f"Error processing URLs in a task for job {self.job_id}: {task_err}", exc_info=True)


        except asyncio.CancelledError:
            logger.info(f"Crawl job {self.job_id} was cancelled/stopped.")
            crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="failed") # Consider a 'stopped' status
        except Exception as e:
            logger.error(f"Critical error during crawl job {self.job_id}: {e}", exc_info=True)
            try:
                 crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status="failed")
            except Exception as db_e:
                logger.error(f"Failed to update job status to 'failed' for job {self.job_id} after critical error: {db_e}")
        finally:
            # Final status update (only if not already stopped/failed)
            if not self._should_stop_event.is_set():
                final_status = "failed" # Default to failed if error occurred before this block
                try:
                    # Re-fetch current status to avoid overwriting stop/fail
                    current_db_status = self.db.query(models.CrawlJob.status).filter(models.CrawlJob.id == self.job_id).scalar()
                    if current_db_status == "running": # Only update if it was still considered running
                        if files_found_count > 0:
                             final_status = "completed"
                        elif self.initial_urls_found: # Found URLs initially but no matching files yielded
                             final_status = "completed_empty"
                        else: # Found no initial URLs AND yielded no files
                             final_status = "completed_empty" # Or potentially 'failed' if no seeds/dorks were valid?
                        crud.update_crawl_job_status(db=self.db, job_id=self.job_id, status=final_status)
                        logger.info(f"Crawl job {self.job_id} finished naturally. Final status: {final_status}. Files yielded: {files_found_count}")
                    else:
                         logger.info(f"Job {self.job_id} status was already '{current_db_status}'. Not overriding final status.")
                except Exception as final_status_err:
                     logger.error(f"Error during final status update for job {self.job_id}: {final_status_err}", exc_info=True)


            # Ensure HTTP client is closed
            if self.http_client and not self.http_client.is_closed:
                await self.http_client.aclose()
                logger.info(f"HTTP client closed for job {self.job_id}.")

            end_time = time.monotonic()
            logger.info(f"Total execution time for job {self.job_id}: {end_time - start_time:.2f} seconds.")


    async def _collect_async_gen(self, agen: AsyncGenerator[str, None]) -> List[str]:
        """Helper to collect items from an async generator into a list."""
        items = []
        try:
            async for item in agen:
                if await self._check_if_stopped(): break
                items.append(item)
        except Exception as e:
            # Log error but allow crawl to continue with results from other generators
            logger.error(f"Error collecting from an async generator: {e}", exc_info=True)
        return items

    # --- Placeholder for robots.txt logic ---
    # async def is_allowed_by_robots(self, url: str) -> bool:
    #     """Checks if crawling the URL is permitted by the domain's robots.txt."""
    #     # This needs implementation: fetch robots.txt, parse, check against URL and User-Agent
    #     # Consider caching robots.txt content per domain.
    #     # Libraries like 'reppy' or manual parsing can be used.
    #     logger.debug(f"Robots.txt check not implemented for {url}. Allowing crawl.")
    #     return True # Default to allow if not implemented
    # ----------------------------------------
