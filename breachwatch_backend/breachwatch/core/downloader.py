import logging
import httpx
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

# Ensure the base download directory exists
DOWNLOAD_BASE_DIR = Path(config.OUTPUT_LOCATIONS_DOWNLOADED_FILES)
DOWNLOAD_BASE_DIR.mkdir(parents=True, exist_ok=True)


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
    job_download_dir = DOWNLOAD_BASE_DIR / str(crawl_job_id)
    job_download_dir.mkdir(parents=True, exist_ok=True)

    local_filename = file_meta.name if file_meta.name else f"{uuid.uuid4().hex}.{file_meta.extension or 'dat'}"
    # Sanitize filename to prevent path traversal or invalid characters
    local_filename = "".join(c if c.isalnum() or c in ('.', '_', '-') else '_' for c in local_filename)
    if not local_filename: # Handle case where sanitization results in empty name
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
            async with client.stream("GET", file_url, follow_redirects=True) as response: # Ensure redirects are followed for downloads
                response.raise_for_status()

                with open(local_file_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        md5_hash.update(chunk)
                        file_size_bytes += len(chunk)
        
        checksum_md5_hex = md5_hash.hexdigest()

        if file_size_bytes > 0 : # Only log success if file is not empty
            logger.info(f"Successfully processed and stored {file_url} ({file_size_bytes} bytes) at {local_file_path} with MD5: {checksum_md5_hex}")

            project_base_dir_parent = Path(config.APP_BASE_DIR).parent if config.APP_BASE_DIR else Path.cwd()
            relative_local_path = str(local_file_path.relative_to(project_base_dir_parent))

            download_entry = DownloadedFileSchema(
                id=uuid.uuid4(), 
                source_url=file_url, 
                file_url=file_url,
                file_type=file_meta.extension,
                date_found=datetime.utcnow(), # This is discovery time by crawler
                keywords_found=keywords_found_triggering_download,
                crawl_job_id=crawl_job_id,
                downloaded_at=datetime.utcnow(), # This is when download/processing finished
                local_path=relative_local_path,
                file_size_bytes=file_size_bytes,
                checksum_md5=checksum_md5_hex,
            )
            return download_entry
        else:
            logger.warning(f"Downloaded file {file_url} is empty. Not creating DB record.")
            if local_file_path.exists():
                os.remove(local_file_path) # Clean up empty file
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


# Example usage (conceptual, needs an async context and httpx client)
# async def main():
#     client = httpx.AsyncClient()
#     test_url = "https://speed.hetzner.de/100MB.bin" # A public test file
#     meta = FileMetadata(name="100MB.bin", extension="bin", mime_type="application/octet-stream")
#     job_id = uuid.uuid4()
#     keywords = ["test_file"]
    
#     result = await download_and_store_file(client, test_url, meta, job_id, keywords)
#     if result:
#         print(f"Download successful: {result.local_path}, Size: {result.file_size_bytes}")
#     else:
#         print("Download failed.")
#     await client.aclose()

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(main())
