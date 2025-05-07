
import logging
import httpx # type: ignore
import os
import uuid
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Optional, List

from breachwatch.utils.config_loader import get_settings
from breachwatch.core.file_identifier import FileMetadata
from breachwatch.api.v1.schemas import DownloadedFileSchema # For return type

logger = logging.getLogger(__name__)
config = get_settings()

# DOWNLOAD_BASE_DIR is now an absolute Path object from settings
DOWNLOAD_BASE_DIR = config.OUTPUT_LOCATIONS.downloaded_files
# Ensure the base download directory exists (e.g. /app/data/downloaded_files or local equivalent)
# This top-level directory might not contain the crawl_job_id yet.
DOWNLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)
logger.info(f"Downloader initialized. Base download directory: {DOWNLOAD_BASE_DIR}")


async def download_and_store_file(
    client: httpx.AsyncClient, 
    file_url: str,
    file_meta: FileMetadata,
    crawl_job_id: uuid.UUID,
    keywords_found_triggering_download: List[str],
    existing_content_bytes: Optional[bytes] = None # Optimization: if crawler already fetched small file
) -> Optional[DownloadedFileSchema]:
    """
    Downloads a file from a given URL (or uses existing_content_bytes if provided), 
    stores it locally, and returns metadata for database logging.
    """
    # job_download_dir will be like /app/data/downloaded_files/<crawl_job_id>
    job_download_dir = DOWNLOAD_BASE_DIR / str(crawl_job_id)
    job_download_dir.mkdir(parents=True, exist_ok=True) # Ensure job-specific dir exists

    local_filename = file_meta.name if file_meta.name else f"{uuid.uuid4().hex}.{file_meta.extension or 'dat'}"
    # Sanitize filename to prevent path traversal or invalid characters
    local_filename = "".join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in local_filename)
    # Ensure filename is not excessively long
    max_filename_len = 100 # Or OS dependent limit
    if len(local_filename) > max_filename_len:
        name_part, ext_part = os.path.splitext(local_filename)
        name_part = name_part[:max_filename_len - len(ext_part) -1] # -1 for the dot
        local_filename = name_part + ext_part

    if not local_filename.strip() or local_filename.strip() == ".": # Handle case where sanitization results in empty/invalid name
        local_filename = f"{uuid.uuid4().hex}.{file_meta.extension or 'dat'}"

    local_file_path = job_download_dir / local_filename
    
    file_size_bytes = 0
    checksum_md5_hex = None

    try:
        md5_hash = hashlib.md5()

        if existing_content_bytes and len(existing_content_bytes) > 0:
            logger.info(f"Using pre-fetched content for: {file_url} to {local_file_path}")
            with open(local_file_path, "wb") as f:
                f.write(existing_content_bytes)
            md5_hash.update(existing_content_bytes)
            file_size_bytes = len(existing_content_bytes)
        else:
            logger.info(f"Attempting to download: {file_url} to {local_file_path}")
            # Using longer timeout for downloads
            async with client.stream("GET", file_url, follow_redirects=True, timeout=config.REQUEST_TIMEOUT * 3) as response: 
                response.raise_for_status()

                # Check for excessive file size early (optional, depends on policy)
                # content_length = response.headers.get('Content-Length')
                # if content_length and int(content_length) > MAX_FILE_SIZE_BYTES:
                #     logger.warning(f"File {file_url} exceeds max size ({content_length} bytes). Skipping.")
                #     return None
                
                with open(local_file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        md5_hash.update(chunk)
                        file_size_bytes += len(chunk)
                        # Add check here for runaway file sizes during streaming if needed
        
        checksum_md5_hex = md5_hash.hexdigest()

        if file_size_bytes > 0 : # Only log success if file is not empty
            logger.info(f"Successfully processed and stored {file_url} ({file_size_bytes} bytes) at {local_file_path} with MD5: {checksum_md5_hex}")

            # Store path relative to a known point for portability if needed, or absolute.
            # For Docker, an absolute path within the container is fine, mapped by volume.
            # If APP_BASE_DIR is /app in container, this path will be like /app/data/downloaded_files/...
            # If not in Docker, it's relative to the host's project root.
            # The key is that it's reconstructible or directly usable by the server.
            
            # Path to store in DB. For Docker, this is the path *inside the container*.
            db_local_path = str(local_file_path)
            
            # If you need a path relative to the *backend project root* for some reason:
            # backend_project_root_in_container = Path(config.APP_BASE_DIR)
            # try:
            #    relative_to_backend_root = str(local_file_path.relative_to(backend_project_root_in_container))
            #    db_local_path = relative_to_backend_root
            # except ValueError: # If not a subpath (shouldn't happen with current setup)
            #    logger.warning(f"Local path {local_file_path} is not relative to APP_BASE_DIR {backend_project_root_in_container}. Storing absolute path.")
            #    db_local_path = str(local_file_path)


            download_entry = DownloadedFileSchema(
                id=uuid.uuid4(), 
                source_url=str(file_url),  # Ensure HttpUrl is converted to str
                file_url=str(file_url),    # Ensure HttpUrl is converted to str
                file_type=file_meta.extension,
                date_found=datetime.utcnow(), # This is discovery time by crawler
                keywords_found=keywords_found_triggering_download,
                crawl_job_id=crawl_job_id,
                downloaded_at=datetime.utcnow(), # This is when download/processing finished
                local_path=db_local_path, # Path inside the container (or local system if not Docker)
                file_size_bytes=file_size_bytes,
                checksum_md5=checksum_md5_hex,
            )
            return download_entry
        else:
            logger.warning(f"Downloaded file {file_url} is empty. Not creating DB record.")
            if local_file_path.exists():
                try:
                    os.remove(local_file_path) # Clean up empty file
                except OSError as e_rm:
                    logger.error(f"Could not remove empty file {local_file_path}: {e_rm}")
            return None


    except httpx.RequestError as e:
        logger.error(f"HTTP request error downloading {file_url}: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error {e.response.status_code} downloading {file_url}: {e.response.text[:200]}")
    except IOError as e:
        logger.error(f"IO error saving file {local_file_path} from {file_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {file_url}: {e}", exc_info=True)
    
    if local_file_path.exists() and (file_size_bytes == 0 or checksum_md5_hex is None): 
        try:
            os.remove(local_file_path)
            logger.info(f"Removed partially downloaded or failed file: {local_file_path}")
        except OSError as e_os:
            logger.error(f"Error removing failed file {local_file_path}: {e_os}")
            
    return None

