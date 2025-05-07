
import os
import yaml
from pydantic import BaseModel, PostgresDsn, validator, Field # type: ignore
from typing import Optional, List, Any
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Determine the base directory of the backend project
# This assumes config_loader.py is in breachwatch/utils/
# So, project_root will be breachwatch_backend/
PROJECT_ROOT_HOST = Path(__file__).resolve().parent.parent.parent

# Load .env file from the project root of the backend
env_path = PROJECT_ROOT_HOST / '.env'
if env_path.exists():
    logger.debug(f"Loading .env file from: {env_path}")
    load_dotenv(dotenv_path=env_path)
else:
    logger.debug(f".env file not found at: {env_path}. Using environment variables or defaults.")


class CrawlerSettings(BaseModel):
    default_delay_seconds: float = 1.0
    max_concurrent_requests_per_domain: int = 2
    max_crawl_depth: int = 3

class OutputLocationsSettings(BaseModel):
    downloaded_files: Path # Path will be resolved to absolute

    @validator("downloaded_files", pre=True)
    def resolve_downloaded_files_path(cls, v: str, values: dict) -> Path:
        app_base_dir_str = values.get("APP_BASE_DIR", str(PROJECT_ROOT_HOST))
        app_base_dir = Path(app_base_dir_str)
        
        path_val = Path(v)
        if not path_val.is_absolute():
            # If APP_BASE_DIR is /app (like in Docker), and v is data/downloaded_files
            # this becomes /app/data/downloaded_files
            # If APP_BASE_DIR is PROJECT_ROOT_HOST (local non-Docker), and v is data/downloaded_files
            # this becomes /path/to/breachwatch_backend/data/downloaded_files
            return (app_base_dir / v).resolve()
        return path_val.resolve()


class AppSettings(BaseModel):
    APP_NAME: str = Field("BreachWatch Backend", alias="app_name")
    APP_VERSION: str = Field("0.1.0", alias="version")
    
    # APP_BASE_DIR should be the root of the backend application.
    # Inside Docker, this is typically /app. Outside Docker, it's PROJECT_ROOT_HOST.
    # It's used by OutputLocationsSettings to resolve relative paths.
    APP_BASE_DIR: str = Field(default_factory=lambda: os.getenv("APP_BASE_DIR", str(PROJECT_ROOT_HOST)))


    DATABASE_URL: Optional[PostgresDsn] = None
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    DB_HOST: Optional[str] = os.getenv("DB_HOST")
    DB_PORT: Optional[str] = os.getenv("DB_PORT") # Store as string, convert to int later if needed
    DB_NAME: Optional[str] = os.getenv("DB_NAME")
    
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    DEFAULT_USER_AGENT: str = os.getenv("DEFAULT_USER_AGENT", "BreachWatchResearchBot/1.0")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 10)) # seconds

    # Nested settings from YAML (or defaults)
    CRAWLER: CrawlerSettings = Field(default_factory=CrawlerSettings) # alias="crawler"
    OUTPUT_LOCATIONS: OutputLocationsSettings # alias="output_locations"

    TARGET_FILE_EXTENSIONS: List[str] = Field(default_factory=lambda: [".txt", ".csv", ".sql"]) # alias="target_file_extensions"
    KEYWORDS_FOR_ANALYSIS: List[str] = Field(default_factory=lambda: ["password", "secret"]) # alias="keywords_for_analysis"


    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str) and v.strip(): # If DATABASE_URL is directly provided and not empty
            return v
        
        # Try to assemble from individual components if DATABASE_URL is not set
        # Values from os.getenv are already in values dict due to Field defaults
        db_user = values.get("DB_USER")
        db_password = values.get("DB_PASSWORD")
        db_host = values.get("DB_HOST")
        db_port = values.get("DB_PORT", "5432") # Default port if not set
        db_name = values.get("DB_NAME")

        if all([db_user, db_password, db_host, db_port, db_name]):
            return str(PostgresDsn.build( # type: ignore
                scheme="postgresql",
                username=db_user,
                password=db_password,
                host=db_host,
                port=int(db_port), 
                path=f"/{db_name}",
            ))
        logger.warning("DATABASE_URL is not set and couldn't be assembled from components. DB operations might fail.")
        return None # Return None if cannot be assembled

    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"
        case_sensitive = False 
        extra = "ignore" 
        populate_by_name = True # Allow using alias if defined, but we removed aliases for nested for simplicity

_settings_instance: Optional[AppSettings] = None

def load_yaml_config(config_path: Path) -> dict:
    if config_path.exists():
        with open(config_path, 'r') as f:
            try:
                yaml_data = yaml.safe_load(f)
                return yaml_data if yaml_data else {} # Ensure it's a dict
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML config file {config_path}: {e}")
    return {}

def get_settings() -> AppSettings:
    global _settings_instance
    if _settings_instance is None:
        # Base dir for APP_BASE_DIR (used for resolving relative paths like downloaded_files)
        # This is set before AppSettings model instantiation.
        app_base_dir_env = os.getenv("APP_BASE_DIR")
        # If APP_BASE_DIR is not set in env, default to host's project root.
        # This is crucial for OutputLocationsSettings path resolution.
        effective_app_base_dir = app_base_dir_env if app_base_dir_env else str(PROJECT_ROOT_HOST)


        yaml_config_path = PROJECT_ROOT_HOST / "config" / "default_config.yml"
        yaml_data = load_yaml_config(yaml_config_path)
        logger.debug(f"Loaded YAML config data: {yaml_data}")

        # Prepare initial data for Pydantic by overlaying sources.
        # Pydantic handles direct env var overrides for top-level fields.
        # For nested structures from YAML, we pass them directly.
        
        initial_data_from_yaml = yaml_data.copy()

        # Pass APP_BASE_DIR explicitly for OUTPUT_LOCATIONS resolver
        if 'output_locations' in initial_data_from_yaml and isinstance(initial_data_from_yaml['output_locations'], dict):
            initial_data_from_yaml['output_locations']['APP_BASE_DIR'] = effective_app_base_dir
        elif 'output_locations' not in initial_data_from_yaml : # Ensure output_locations exists for validator
             initial_data_from_yaml['output_locations'] = {'downloaded_files': 'data/downloaded_files', 'APP_BASE_DIR': effective_app_base_dir}


        # Allow environment variables to override YAML for top-level simple fields
        # Pydantic does this automatically if env vars match field names (case-insensitive).
        # For nested fields, we rely on the structure from YAML or Pydantic defaults.
        
        # Construct AppSettings. Pydantic will:
        # 1. Use default_factory for fields like CRAWLER, etc.
        # 2. Overlay with values from initial_data_from_yaml.
        # 3. Overlay with environment variables for matching top-level fields.
        # 4. Run validators (like DATABASE_URL assembler and path resolver).
        
        # Explicitly provide APP_BASE_DIR for the model itself.
        final_initial_data = {"APP_BASE_DIR": effective_app_base_dir, **initial_data_from_yaml}

        try:
            _settings_instance = AppSettings(**final_initial_data) # type: ignore
            logger.info("Application settings loaded successfully.")
            if _settings_instance.DATABASE_URL and _settings_instance.DB_PASSWORD:
                masked_db_url = _settings_instance.DATABASE_URL.replace(_settings_instance.DB_PASSWORD, '********')
                logger.debug(f"Final DATABASE_URL (sensitive part masked): {masked_db_url}")
            elif _settings_instance.DATABASE_URL:
                 logger.debug(f"Final DATABASE_URL: {_settings_instance.DATABASE_URL}")

            logger.debug(f"Downloaded files location: {_settings_instance.OUTPUT_LOCATIONS.downloaded_files}")

        except Exception as e:
            logger.error(f"Error initializing AppSettings with Pydantic: {e}", exc_info=True)
            # Fallback: This is risky as essential configs might be missing.
            # Consider raising an error or exiting if config is critical.
            logger.warning("Attempting to initialize AppSettings with minimal defaults due to error.")
            try:
                # Try to initialize with absolute minimum defaults if primary init fails
                _settings_instance = AppSettings(
                    APP_BASE_DIR=effective_app_base_dir,
                    OUTPUT_LOCATIONS = {'downloaded_files': 'data/downloaded_files/fallback', 'APP_BASE_DIR': effective_app_base_dir } # type: ignore
                )

            except Exception as fallback_e:
                 logger.critical(f"CRITICAL: Could not initialize AppSettings even with fallback: {fallback_e}", exc_info=True)
                 raise RuntimeError(f"Failed to initialize application settings: {fallback_e}") from fallback_e


    return _settings_instance

# Example usage:
if __name__ == "__main__":
    settings = get_settings()
    print("App Name:", settings.APP_NAME)
    print("App Version:", settings.APP_VERSION)
    if settings.DATABASE_URL and settings.DB_PASSWORD:
        print("Database URL (masked):", settings.DATABASE_URL.replace(settings.DB_PASSWORD, '********'))
    elif settings.DATABASE_URL:
        print("Database URL:", settings.DATABASE_URL)
    else:
        print("Database URL: Not configured")
    print("Log Level:", settings.LOG_LEVEL)
    print("Crawler Settings Delay:", settings.CRAWLER.default_delay_seconds)
    print("Downloaded Files Path:", settings.OUTPUT_LOCATIONS.downloaded_files)
    print("Target Extensions:", settings.TARGET_FILE_EXTENSIONS)
    print("App Base Dir used for settings:", settings.APP_BASE_DIR)
    print(f"Project root (host): {PROJECT_ROOT_HOST}")
    print(f"Env path loaded: {env_path}")

    # Test if DATABASE_URL is correctly assembled or used
    if not settings.DATABASE_URL:
         print("\nWARNING: DATABASE_URL is not configured. Database operations will fail.")
         print("Ensure DATABASE_URL is set in .env or individual DB_USER, DB_PASSWORD, etc. are set.")
    else:
        print(f"\nDATABASE_URL is set.")
    
    if settings.DB_PASSWORD:
        print("DB_PASSWORD is set (should be masked in logs).")
    else:
        print("DB_PASSWORD is not set (or not loaded).")
    
    print(f"Resolved output path for downloaded files: {settings.OUTPUT_LOCATIONS.downloaded_files}")
    print(f"Is output path absolute? {settings.OUTPUT_LOCATIONS.downloaded_files.is_absolute()}")
    # Check if the directory exists (it should be created by downloader.py if needed)
    # but config loader should ensure the path object is valid.
    if not settings.OUTPUT_LOCATIONS.downloaded_files.parent.exists():
        print(f"Warning: Parent directory for downloads does not exist: {settings.OUTPUT_LOCATIONS.downloaded_files.parent}")

