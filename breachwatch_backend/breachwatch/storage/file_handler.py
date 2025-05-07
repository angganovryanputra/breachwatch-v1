
import logging
import os
from pathlib import Path
import uuid # For type hinting Job ID

from breachwatch.utils.config_loader import get_settings

logger = logging.getLogger(__name__)
config = get_settings()

# DOWNLOAD_DIR is now an absolute Path from config
DOWNLOAD_DIR_BASE = config.OUTPUT_LOCATIONS.downloaded_files
logger.info(f"File handler using base download directory: {DOWNLOAD_DIR_BASE}")

def get_file_path(crawl_job_id: uuid.UUID, filename: str) -> Path:
    """
    Constructs the full absolute path for a downloaded file within its job-specific directory.
    Ensures the job-specific directory exists.
    """
    job_dir = DOWNLOAD_DIR_BASE / str(crawl_job_id)
    job_dir.mkdir(parents=True, exist_ok=True) # Ensure it exists
    return job_dir / filename

def delete_physical_file(file_path_str: str) -> bool:
    """
    Deletes a file from the filesystem.
    The file_path_str is expected to be an absolute path or a path resolvable
    from the context where this function is called (preferably absolute).
    """
    # The path stored in DB (and thus passed here) should be the one usable by the server.
    # With Docker, this means the path *inside the container*.
    # config_loader.py ensures OUTPUT_LOCATIONS.downloaded_files is absolute.
    # downloader.py stores the absolute path (inside container) to the DB.
    file_path = Path(file_path_str)

    if not file_path.is_absolute():
        logger.warning(f"Received non-absolute path for deletion: {file_path_str}. Attempting to resolve relative to APP_BASE_DIR.")
        # This case should ideally not happen if paths are stored consistently.
        # APP_BASE_DIR is the root of the backend app (e.g., /app in Docker).
        # If local_path was stored relative to this, we reconstruct.
        app_base_path = Path(config.APP_BASE_DIR)
        file_path = (app_base_path / file_path_str).resolve()
        logger.info(f"Resolved path to: {file_path}")


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

if __name__ == '__main__':
    # Example usage (conceptual, assumes a job ID and file)
    # This test will only work if the base download directory is writable.
    
    # Create a dummy job ID
    test_job_id = uuid.uuid4()
    dummy_filename = "test_delete_me.txt"
    
    # Get path (this also creates the job directory)
    path_to_create = get_file_path(test_job_id, dummy_filename)
    print(f"Path for dummy file: {path_to_create}")

    # Create a dummy file
    try:
        with open(path_to_create, "w") as f:
            f.write("This is a test file for deletion.")
        print(f"Created dummy file: {path_to_create}")

        # Test deletion
        deleted = delete_physical_file(str(path_to_create))
        if deleted:
            print(f"Successfully deleted dummy file: {path_to_create}")
            if path_to_create.exists():
                 print(f"ERROR: File {path_to_create} still exists after deletion attempt!")
        else:
            print(f"Failed to delete dummy file: {path_to_create}")
            
        # Clean up job directory if empty (optional)
        job_dir_path = DOWNLOAD_DIR_BASE / str(test_job_id)
        if job_dir_path.exists() and not any(job_dir_path.iterdir()):
            try:
                job_dir_path.rmdir()
                print(f"Cleaned up empty job directory: {job_dir_path}")
            except OSError as e:
                print(f"Could not remove job directory {job_dir_path}: {e}")
        elif job_dir_path.exists():
            print(f"Job directory {job_dir_path} is not empty, not removing.")


    except Exception as e:
        print(f"Error during test: {e}")
