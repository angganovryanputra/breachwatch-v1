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
    client: httpx.AsyncClient, # Pass the shared AsyncClient
    file_url: str,
    file_meta: FileMetadata,
    crawl_job_id: uuid.UUID,
    keywords_found_triggering_download: List[str] # Keywords that led to this download
) -> Optional[DownloadedFileSchema]:
    """
    Downloads a file from a given URL, stores it locally,
    and returns metadata for database logging.
    """
    # Create a unique sub-directory for each crawl job to organize files
    job_download_dir = DOWNLOAD_BASE_DIR / str(crawl_job_id)
    job_download_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize filename and ensure uniqueness if needed, or use a UUID-based name
    # For now, using original name, but could append UUID if collisions are a concern.
    # local_filename = f"{uuid.uuid4().hex}_{file_meta.name}" # Guaranteed unique
    local_filename = file_meta.name if file_meta.name else f"{uuid.uuid4().hex}.{file_meta.extension or 'dat'}"
    local_file_path = job_download_dir / local_filename
    
    file_size_bytes = 0
    checksum_md5_hex = None

    try:
        logger.info(f"Attempting to download: {file_url} to {local_file_path}")
        async with client.stream("GET", file_url) as response:
            response.raise_for_status() # Check for HTTP errors

            md5_hash = hashlib.md5()
            with open(local_file_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
                    md5_hash.update(chunk)
                    file_size_bytes += len(chunk)
            
            checksum_md5_hex = md5_hash.hexdigest()

        logger.info(f"Successfully downloaded {file_url} ({file_size_bytes} bytes) with MD5: {checksum_md5_hex}")

        download_entry = DownloadedFileSchema(
            id=uuid.uuid4(), # This will be the primary key for the DownloadedFile record
            source_url=file_url, # In this context, source_url and file_url are the same
            file_url=file_url,
            file_type=file_meta.extension,
            date_found=datetime.utcnow(), # This should ideally come from the crawler's discovery time
            keywords_found=keywords_found_triggering_download,
            crawl_job_id=crawl_job_id,
            downloaded_at=datetime.utcnow(),
            local_path=str(local_file_path.relative_to(Path(config.APP_BASE_DIR).parent if config.APP_BASE_DIR else Path.cwd())), # Store relative path from project root potentially
            # local_path=str(local_file_path), # Or absolute path
            file_size_bytes=file_size_bytes,
            checksum_md5=checksum_md5_hex,
        )
        return download_entry

    except httpx.RequestError as e:
        logger.error(f"HTTP request error downloading {file_url}: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP status error {e.response.status_code} downloading {file_url}: {e.response.text[:200]}")
    except IOError as e:
        logger.error(f"IO error saving file {local_file_path} from {file_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error downloading {file_url}: {e}", exc_info=True)
    
    # Cleanup partially downloaded file if error occurred
    if local_file_path.exists() and file_size_bytes == 0 : # Or if checksum failed
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
