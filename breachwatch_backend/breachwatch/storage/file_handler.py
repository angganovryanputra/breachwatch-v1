import logging
import os
from pathlib import Path

from breachwatch.utils.config_loader import get_settings

logger = logging.getLogger(__name__)
config = get_settings()

DOWNLOAD_DIR = Path(config.OUTPUT_LOCATIONS_DOWNLOADED_FILES)

def get_file_path(crawl_job_id: str, filename: str) -> Path:
    """Constructs the full path for a downloaded file."""
    return DOWNLOAD_DIR / crawl_job_id / filename

def delete_physical_file(file_path_str: str) -> bool:
    """Deletes a file from the filesystem."""
    file_path = Path(file_path_str)
    if not file_path.is_absolute():
        # Assuming file_path_str is relative to project root or a configured base
        # This needs careful handling based on how paths are stored in DB
        # For now, let's assume it might be relative to DOWNLOAD_DIR
        # A better approach is to store absolute paths or paths relative to a known root in DB
        # For this example, let's assume it's an absolute path or correctly relative to CWD.
        pass


    if file_path.exists() and file_path.is_file():
        try:
            os.remove(file_path)
            logger.info(f"Successfully deleted physical file: {file_path}")
            return True
        except OSError as e:
            logger.error(f"Error deleting physical file {file_path}: {e}")
            return False
    else:
        logger.warning(f"Physical file not found or not a file, cannot delete: {file_path}")
        return False

# Further functions could include:
# - Listing files in a job's directory
# - Getting file size/metadata from disk
# - Archiving old files
# - Moving files to different storage tiers (e.g., cloud)
