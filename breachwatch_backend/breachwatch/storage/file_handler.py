
import logging
import os
from pathlib import Path
import uuid # For type hinting Job ID
import shutil # For deleting directory trees

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
    if not file_path_str:
        logger.warning("Attempted to delete physical file with empty path string.")
        return False
        
    file_path = Path(file_path_str)

    if not file_path.is_absolute():
        logger.warning(f"Received non-absolute path for deletion: {file_path_str}. Attempting to resolve relative to APP_BASE_DIR.")
        app_base_path = Path(config.APP_BASE_DIR)
        file_path = (app_base_path / file_path_str).resolve()
        logger.info(f"Resolved path to: {file_path}")

    try:
        if file_path.exists():
            if file_path.is_file():
                os.remove(file_path)
                logger.info(f"Successfully deleted physical file: {file_path}")
                return True
            else:
                logger.warning(f"Path exists but is not a file, cannot delete: {file_path}")
                return False
        else:
            logger.warning(f"Physical file not found, cannot delete: {file_path}")
            return False
    except OSError as e:
        logger.error(f"Error deleting physical file {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error deleting physical file {file_path}: {e}", exc_info=True)
        return False


def delete_job_directory(crawl_job_id: uuid.UUID) -> bool:
    """
    Deletes the entire download directory for a specific crawl job.
    """
    job_dir = DOWNLOAD_DIR_BASE / str(crawl_job_id)
    logger.info(f"Attempting to delete job directory: {job_dir}")

    if not job_dir.is_absolute(): # Should always be absolute due to DOWNLOAD_DIR_BASE logic
        logger.error(f"Job directory path is not absolute, cannot delete: {job_dir}. This indicates a configuration problem.")
        return False
        
    if job_dir.exists() and job_dir.is_dir():
        try:
            shutil.rmtree(job_dir)
            logger.info(f"Successfully deleted job directory and all its contents: {job_dir}")
            return True
        except OSError as e:
            logger.error(f"Error deleting job directory {job_dir}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting job directory {job_dir}: {e}", exc_info=True)
            return False
    else:
        logger.warning(f"Job directory not found or not a directory, cannot delete: {job_dir}")
        return False


if __name__ == '__main__':
    # Example usage (conceptual, assumes a job ID and file)
    # This test will only work if the base download directory is writable.
    
    # Create a dummy job ID
    test_job_id = uuid.uuid4()
    dummy_filename = "test_delete_me.txt"
    dummy_filename2 = "test_another.log"
    
    # Get path (this also creates the job directory)
    path_to_create = get_file_path(test_job_id, dummy_filename)
    path_to_create2 = get_file_path(test_job_id, dummy_filename2)
    print(f"Path for dummy file: {path_to_create}")

    # Create a dummy file
    try:
        with open(path_to_create, "w") as f:
            f.write("This is a test file for deletion.")
        print(f"Created dummy file: {path_to_create}")
        
        with open(path_to_create2, "w") as f:
            f.write("Another test file.")
        print(f"Created dummy file: {path_to_create2}")


        # Test deletion of a single file
        # deleted_single = delete_physical_file(str(path_to_create))
        # if deleted_single:
        #     print(f"Successfully deleted single dummy file: {path_to_create}")
        #     if path_to_create.exists():
        #          print(f"ERROR: File {path_to_create} still exists after single deletion attempt!")
        # else:
        #     print(f"Failed to delete single dummy file: {path_to_create}")
            
        # Test deletion of job directory
        deleted_job_dir = delete_job_directory(test_job_id)
        if deleted_job_dir:
            print(f"Successfully deleted job directory for job: {test_job_id}")
            job_dir_path_check = DOWNLOAD_DIR_BASE / str(test_job_id)
            if job_dir_path_check.exists():
                 print(f"ERROR: Job directory {job_dir_path_check} still exists after deletion attempt!")
        else:
            print(f"Failed to delete job directory for job: {test_job_id}")


    except Exception as e:
        print(f"Error during test: {e}")

```