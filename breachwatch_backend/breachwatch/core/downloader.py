
import logging
import httpx # type: ignore
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
import hashlib
from typing import Optional, List, Dict

from breachwatch.utils.config_loader import get_settings
from breachwatch.core.file_identifier import FileMetadata
from breachwatch.api.v1.schemas import DownloadedFileSchema # For return type

logger = logging.getLogger(__name__)
config = get_settings()

# DOWNLOAD_BASE_DIR is now an absolute Path object from settings
DOWNLOAD_BASE_DIR = config.OUTPUT_LOCATIONS.downloaded_files
DOWNLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Downloader initialized. Base download directory: {DOWNLOAD_BASE_DIR}")


async def download_and_store_file(
    client: httpx.AsyncClient, 
    file_url: str,
    file_meta: FileMetadata,
    crawl_job_id: uuid.UUID,
    keywords_found_triggering_download: List[str],
    existing_content_bytes: Optional[bytes] = None,
    proxies: Optional[Dict[str, str]] = None # Optional proxies for download if ever needed
) -> Optional[DownloadedFileSchema]:
    """
    Downloads a file, stores it locally, and returns metadata.
    Uses `client` which should be a base client; proxies are applied if passed.
    """
    job_download_dir = DOWNLOAD_BASE_DIR / str(crawl_job_id)
    job_download_dir.mkdir(parents=True, exist_ok=True)

    local_filename = file_meta.name if file_meta.name else f"{uuid.uuid4().hex}.{file_meta.extension or 'dat'}"
    local_filename = "".join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in local_filename)
    max_filename_len = 100
    if len(local_filename) > max_filename_len:
        name_part, ext_part = os.path.splitext(local_filename)
        name_part = name_part[:max_filename_len - len(ext_part) -1]
        local_filename = name_part + ext_part
    if not local_filename.strip() or local_filename.strip() == ".":
        local_filename = f"{uuid.uuid4().hex}.{file_meta.extension or 'dat'}"
    local_file_path = job_download_dir / local_filename
    
    file_size_bytes = 0
    checksum_md5_hex = None

    try:
        md5_hash = hashlib.md5()

        if existing_content_bytes and len(existing_content_bytes) > 0:
            logger.info(f"Using pre-fetched content for: {file_url} to {local_file_path}")
            with open(local_file_path, "wb") as f: f.write(existing_content_bytes)
            md5_hash.update(existing_content_bytes)
            file_size_bytes = len(existing_content_bytes)
        else:
            logger.info(f"Attempting to download: {file_url} to {local_file_path} {'with proxies' if proxies else ''}")
            # Use a longer timeout for downloads, inherit client's default if not specified
            download_timeout = httpx.Timeout(config.REQUEST_TIMEOUT * 3, connect=config.REQUEST_TIMEOUT)
            
            # Use the passed client, applying proxies if provided
            async with client.stream("GET", file_url, follow_redirects=True, timeout=download_timeout, proxies=proxies) as response: 
                response.raise_for_status()
                with open(local_file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        md5_hash.update(chunk)
                        file_size_bytes += len(chunk)
        
        checksum_md5_hex = md5_hash.hexdigest()

        if file_size_bytes > 0 :
            logger.info(f"Processed {file_url} ({file_size_bytes}B) at {local_file_path}, MD5: {checksum_md5_hex}")
            db_local_path = str(local_file_path)
            
            download_entry = DownloadedFileSchema(
                id=uuid.uuid4(), 
                source_url=str(file_url),
                file_url=str(file_url),
                file_type=file_meta.extension,
                date_found=datetime.now(timezone.utc), # Discovery time by crawler
                keywords_found=keywords_found_triggering_download,
                crawl_job_id=crawl_job_id,
                downloaded_at=datetime.now(timezone.utc), # Processing finished time
                local_path=db_local_path,
                file_size_bytes=file_size_bytes,
                checksum_md5=checksum_md5_hex,
            )
            return download_entry
        else:
            logger.warning(f"Downloaded file {file_url} is empty. Not creating DB record.")
            if local_file_path.exists():
                try: os.remove(local_file_path)
                except OSError as e_rm: logger.error(f"Could not remove empty file {local_file_path}: {e_rm}")
            return None

    except httpx.ProxyError as e:
        logger.error(f"Proxy error during download of {file_url} with proxies {proxies}: {e}")
    except httpx.RequestError as e:
        logger.error(f"HTTP request error downloading {file_url}: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status {e.response.status_code} downloading {file_url}: {e.response.text[:200]}")
    except IOError as e:
        logger.error(f"IO error saving file {local_file_path} from {file_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {file_url}: {e}", exc_info=True)
    
    if local_file_path.exists() and (file_size_bytes == 0 or checksum_md5_hex is None): 
        try:
            os.remove(local_file_path)
            logger.info(f"Removed partially downloaded or failed file: {local_file_path}")
        except OSError as e_os: logger.error(f"Error removing failed file {local_file_path}: {e_os}")
            
    return None

    