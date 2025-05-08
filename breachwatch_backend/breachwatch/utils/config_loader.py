
import os
import yaml
from pydantic import BaseModel, PostgresDsn, validator, Field # type: ignore
from typing import Optional, List, Any
from pathlib import Path
from dotenv import load_dotenv
import logging
import secrets # For generating default secret key if not set

logger = logging.getLogger(__name__)

# Determine the base directory of the backend project
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
        # Need APP_BASE_DIR to resolve relative paths correctly
        app_base_dir_str = values.get("APP_BASE_DIR")
        if not app_base_dir_str:
            # If APP_BASE_DIR isn't available during validation (should be), fallback or raise error
            # logger.warning("APP_BASE_DIR not found during OutputLocationsSettings validation. Using host root.")
            app_base_dir = PROJECT_ROOT_HOST
        else:
             app_base_dir = Path(app_base_dir_str)

        path_val = Path(v)
        if not path_val.is_absolute():
            resolved_path = (app_base_dir / v).resolve()
            logger.debug(f"Resolved relative path '{v}' to '{resolved_path}' using base '{app_base_dir}'")
            return resolved_path
        return path_val.resolve()


class AppSettings(BaseModel):
    APP_NAME: str = Field("BreachWatch Backend", alias="app_name")
    APP_VERSION: str = Field("0.1.0", alias="version")
    ENVIRONMENT: str = Field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))

    # APP_BASE_DIR should be the root of the backend application.
    APP_BASE_DIR: str = Field(default_factory=lambda: os.getenv("APP_BASE_DIR", str(PROJECT_ROOT_HOST)))

    # Database Configuration
    DATABASE_URL: Optional[PostgresDsn] = None
    DB_USER: Optional[str] = os.getenv("DB_USER")
    DB_PASSWORD: Optional[str] = os.getenv("DB_PASSWORD")
    DB_HOST: Optional[str] = os.getenv("DB_HOST")
    DB_PORT: Optional[str] = os.getenv("DB_PORT") # Store as string, convert to int later if needed
    DB_NAME: Optional[str] = os.getenv("DB_NAME")

    # Redis Configuration for Caching
    REDIS_HOST: str = Field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    REDIS_PORT: int = Field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    REDIS_DB: int = Field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))

    # API & Logging
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Crawler & Network Defaults
    DEFAULT_USER_AGENT: str = os.getenv("DEFAULT_USER_AGENT", "BreachWatchResearchBot/1.0")
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 10)) # seconds

    # JWT Authentication Settings
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY", secrets.token_hex(32)))
    ALGORITHM: str = Field(default_factory=lambda: os.getenv("ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


    # Nested settings from YAML (or defaults) - Load these after base fields
    CRAWLER: CrawlerSettings = Field(default_factory=CrawlerSettings)
    OUTPUT_LOCATIONS: OutputLocationsSettings

    # Default lists if not in YAML or ENV (though less common to set lists via ENV)
    TARGET_FILE_EXTENSIONS: List[str] = Field(default_factory=lambda: [".txt", ".csv", ".sql"])
    KEYWORDS_FOR_ANALYSIS: List[str] = Field(default_factory=lambda: ["password", "secret"])


    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str) and v.strip(): # If DATABASE_URL is directly provided and not empty
            logger.debug("Using provided DATABASE_URL.")
            return v

        # Try to assemble from individual components if DATABASE_URL is not set
        db_user = values.get("DB_USER")
        db_password = values.get("DB_PASSWORD")
        db_host = values.get("DB_HOST")
        db_port = values.get("DB_PORT")
        db_name = values.get("DB_NAME")

        if not db_port:
             logger.debug("DB_PORT not set, using default 5432.")
             db_port = "5432"

        if all([db_user, db_password, db_host, db_port, db_name]):
            try:
                constructed_url = str(PostgresDsn.build( # type: ignore
                    scheme="postgresql",
                    username=db_user,
                    password=db_password,
                    host=db_host,
                    port=int(db_port),
                    path=f"/{db_name}",
                ))
                logger.debug("Assembled DATABASE_URL from components.")
                return constructed_url
            except ValueError as e:
                 logger.error(f"Error converting DB_PORT '{db_port}' to integer: {e}")
                 logger.warning("Could not assemble DATABASE_URL due to port conversion error.")
                 return None
            except Exception as e:
                logger.error(f"Error building DATABASE_URL: {e}")
                return None
        else:
             # Log which components are missing
             missing = [comp for comp in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_NAME"] if not values.get(comp)]
             if not values.get("DB_PORT"): missing.append("DB_PORT (using default 5432 if others present)")
             logger.warning(f"DATABASE_URL is not set and couldn't be assembled. Missing components: {', '.join(missing)}. DB operations might fail.")
             return None # Return None if cannot be assembled


    @validator("SECRET_KEY", always=True)
    def check_secret_key(cls, v: Optional[str]) -> str:
        if v is None or len(v) < 32: # Check length for minimum security
             logger.warning("SECRET_KEY is not set or is too short. Generating a temporary secure key. Set a persistent SECRET_KEY in your .env file for production!")
             return secrets.token_hex(32)
        # Don't log the key itself, just check it was provided
        if os.getenv("SECRET_KEY") == v:
             logger.debug("Using SECRET_KEY from environment.")
        else:
             logger.debug("Using generated SECRET_KEY (or one from non-standard source).")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
        populate_by_name = True # Allows using alias (though we removed most aliases)

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
        # Determine APP_BASE_DIR first as it's needed by OutputLocationsSettings validator
        effective_app_base_dir = os.getenv("APP_BASE_DIR", str(PROJECT_ROOT_HOST))

        # Load YAML config
        yaml_config_path = PROJECT_ROOT_HOST / "config" / "default_config.yml"
        yaml_data = load_yaml_config(yaml_config_path)
        logger.debug(f"Loaded YAML config data: {yaml_data}")

        # Prepare initial data, ensuring nested structures are handled
        initial_data = {
            "APP_BASE_DIR": effective_app_base_dir, # Ensure base dir is set
            "CRAWLER": yaml_data.get("crawler", {}), # Pass nested dict or empty
            "OUTPUT_LOCATIONS": yaml_data.get("output_locations", {"downloaded_files": "data/downloaded_files/fallback"}), # Pass nested dict or default fallback path string
             "TARGET_FILE_EXTENSIONS": yaml_data.get("target_file_extensions"), # Pass list or None
             "KEYWORDS_FOR_ANALYSIS": yaml_data.get("keywords_for_analysis"), # Pass list or None
             # Pass other top-level YAML fields if they exist
             "app_name": yaml_data.get("app_name"),
             "version": yaml_data.get("version"),
             # ENV vars will override these if set, via Pydantic's loading mechanism
        }
         # Ensure OUTPUT_LOCATIONS contains APP_BASE_DIR for its validator
        if 'OUTPUT_LOCATIONS' in initial_data and isinstance(initial_data['OUTPUT_LOCATIONS'], dict):
            initial_data["OUTPUT_LOCATIONS"]["APP_BASE_DIR"] = effective_app_base_dir
        elif 'OUTPUT_LOCATIONS' in initial_data: # If it exists but is not a dict (e.g. just the path string)
             # This path shouldn't normally be hit with current logic, but handle defensively
             logger.warning("OUTPUT_LOCATIONS in YAML was not a dictionary. Trying to handle.")
             output_path = initial_data['OUTPUT_LOCATIONS']
             initial_data['OUTPUT_LOCATIONS'] = {'downloaded_files': str(output_path), 'APP_BASE_DIR': effective_app_base_dir}
        else: # If not present at all
              initial_data['OUTPUT_LOCATIONS'] = {'downloaded_files': 'data/downloaded_files/fallback', 'APP_BASE_DIR': effective_app_base_dir}


        # Pydantic will now initialize using:
        # 1. Field defaults (like os.getenv calls, default_factory)
        # 2. Values from `initial_data` (YAML content)
        # 3. Environment variables (overriding YAML and defaults for matching fields)
        # 4. Run validators

        try:
            _settings_instance = AppSettings(**initial_data) # type: ignore
            logger.info(f"Application settings loaded successfully for environment: {_settings_instance.ENVIRONMENT}")
            if _settings_instance.DATABASE_URL and _settings_instance.DB_PASSWORD:
                masked_db_url = _settings_instance.DATABASE_URL.replace(_settings_instance.DB_PASSWORD, '********')
                logger.debug(f"Final DATABASE_URL (sensitive part masked): {masked_db_url}")
            elif _settings_instance.DATABASE_URL:
                 logger.debug(f"Final DATABASE_URL: {_settings_instance.DATABASE_URL}")

            logger.debug(f"Downloaded files location: {_settings_instance.OUTPUT_LOCATIONS.downloaded_files}")
            logger.debug(f"Log Level set to: {_settings_instance.LOG_LEVEL}")
            logger.debug(f"Redis configured at: {_settings_instance.REDIS_HOST}:{_settings_instance.REDIS_PORT} (DB: {_settings_instance.REDIS_DB})")


        except Exception as e:
            logger.error(f"Error initializing AppSettings with Pydantic: {e}", exc_info=True)
            logger.critical(f"CRITICAL: Could not initialize AppSettings. Check configuration (.env, YAML). Error: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize application settings: {e}") from e


    return _settings_instance

# Example usage:
if __name__ == "__main__":
    settings = get_settings()
    print("App Name:", settings.APP_NAME)
    print("App Version:", settings.APP_VERSION)
    print("Environment:", settings.ENVIRONMENT)
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

    print(f"Secret Key is set: {'Yes' if settings.SECRET_KEY else 'No'}")
    print(f"JWT Algorithm: {settings.ALGORITHM}")
    print(f"Token Expiry (minutes): {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")

    print(f"Resolved output path for downloaded files: {settings.OUTPUT_LOCATIONS.downloaded_files}")
    print(f"Is output path absolute? {settings.OUTPUT_LOCATIONS.downloaded_files.is_absolute()}")
    if not settings.OUTPUT_LOCATIONS.downloaded_files.parent.exists():
        print(f"Warning: Parent directory for downloads does not exist: {settings.OUTPUT_LOCATIONS.downloaded_files.parent}")

    print(f"Redis Host: {settings.REDIS_HOST}")
    print(f"Redis Port: {settings.REDIS_PORT}")
    print(f"Redis DB: {settings.REDIS_DB}")
    print(f"Redis Password Set: {'Yes' if settings.REDIS_PASSWORD else 'No'}")
