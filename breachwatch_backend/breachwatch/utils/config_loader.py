import os
import yaml
from pydantic import BaseModel, PostgresDsn, validator, Field
from typing import Optional, List, Any
from pathlib import Path
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Determine the base directory of the backend project
# This assumes config_loader.py is in breachwatch/utils/
# So, project_root will be breachwatch_backend/
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load .env file from the project root
env_path = PROJECT_ROOT / '.env'
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
    downloaded_files: str = "data/downloaded_files"
    # metadata_db_path: str = "data/metadata_db/breachwatch_metadata.sqlite" # For SQLite if used

class AppSettings(BaseModel):
    APP_NAME: str = Field("BreachWatch Backend", alias="app_name")
    APP_VERSION: str = Field("0.1.0", alias="version")
    APP_BASE_DIR: Optional[str] = str(PROJECT_ROOT)

    DATABASE_URL: Optional[PostgresDsn] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[str] = None # Store as string, convert to int later if needed
    DB_NAME: Optional[str] = None
    
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    DEFAULT_USER_AGENT: str = "BreachWatchResearchBot/1.0"
    REQUEST_TIMEOUT: int = 10 # seconds

    # Nested settings from YAML (or defaults)
    CRAWLER: CrawlerSettings = Field(default_factory=CrawlerSettings, alias="crawler")
    OUTPUT_LOCATIONS: OutputLocationsSettings = Field(default_factory=OutputLocationsSettings, alias="output_locations")

    TARGET_FILE_EXTENSIONS: List[str] = Field(default_factory=lambda: [".txt", ".csv", ".sql"], alias="target_file_extensions")
    KEYWORDS_FOR_ANALYSIS: List[str] = Field(default_factory=lambda: ["password", "secret"], alias="keywords_for_analysis")


    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str): # If DATABASE_URL is directly provided
            return v
        
        # Try to assemble from individual components if DATABASE_URL is not set
        db_user = values.get("DB_USER") or os.getenv("DB_USER")
        db_password = values.get("DB_PASSWORD") or os.getenv("DB_PASSWORD")
        db_host = values.get("DB_HOST") or os.getenv("DB_HOST")
        db_port = values.get("DB_PORT") or os.getenv("DB_PORT", "5432")
        db_name = values.get("DB_NAME") or os.getenv("DB_NAME")

        if all([db_user, db_password, db_host, db_port, db_name]):
            return str(PostgresDsn.build(
                scheme="postgresql",
                username=db_user,
                password=db_password,
                host=db_host,
                port=int(db_port), # Pydantic model expects int here
                path=f"/{db_name}",
            ))
        return v # Return None or existing v if components are not fully available


    class Config:
        env_file = ".env" # Pydantic can also load from .env, but load_dotenv is more explicit for path
        env_file_encoding = "utf-8"
        case_sensitive = False # For environment variable names
        extra = "ignore" # Ignore extra fields from YAML or env that are not in the model
        populate_by_name = True # Allow using alias for field population


_settings_instance: Optional[AppSettings] = None

def load_yaml_config(config_path: Path) -> dict:
    if config_path.exists():
        with open(config_path, 'r') as f:
            try:
                return yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML config file {config_path}: {e}")
    return {}

def get_settings() -> AppSettings:
    global _settings_instance
    if _settings_instance is None:
        # Load from environment first (Pydantic does this automatically if fields match env vars)
        # Then, load from YAML, allowing env to override YAML if Pydantic loads env first.
        # The order matters. Pydantic's default is: init -> env -> .env file (if configured in Config)

        # 1. Load YAML config as a base
        yaml_config_path = PROJECT_ROOT / "config" / "default_config.yml"
        yaml_data = load_yaml_config(yaml_config_path)
        logger.debug(f"Loaded YAML config data: {yaml_data}")

        # 2. Create AppSettings instance. Pydantic will:
        #    - Use init values (if any, none here)
        #    - Override with values from the `yaml_data` dictionary if field names match
        #    - Override with environment variables if names match (case-insensitive by default)
        #    - Override with .env file (if `env_file` is set in Pydantic's Config and Pydantic loads it,
        #      but we loaded it manually with `load_dotenv` earlier which is generally fine).
        # The `alias` in Field definitions helps map YAML keys to model fields.
        
        # We need to handle nested structures from YAML carefully.
        # Pydantic expects flat dicts for env vars, but can take nested for init.
        
        # Prepare initial data by merging YAML and env variables where Pydantic might not auto-map nested.
        initial_data = yaml_data.copy()

        # Manually overlay environment variables for top-level fields to ensure they take precedence if set.
        # Pydantic should handle this, but this makes it explicit for clarity.
        for field_name, field in AppSettings.model_fields.items():
            env_var_name = field.alias or field_name
            env_value = os.getenv(env_var_name.upper()) # Try uppercase for env vars
            if env_value is not None:
                # Try to cast to the correct type if it's a simple type.
                # Pydantic will do more robust casting later.
                if field.annotation == int:
                    try: initial_data[field_name] = int(env_value)
                    except ValueError: pass
                elif field.annotation == bool:
                    initial_data[field_name] = env_value.lower() in ['true', '1', 'yes']
                elif field.annotation == float:
                    try: initial_data[field_name] = float(env_value)
                    except ValueError: pass
                elif field.annotation == List[str]:
                    initial_data[field_name] = [s.strip() for s in env_value.split(',')]
                else:
                     initial_data[field_name] = env_value
        
        # Special handling for DATABASE_URL as it can be assembled or direct
        if os.getenv("DATABASE_URL"):
            initial_data["DATABASE_URL"] = os.getenv("DATABASE_URL")
        elif all(os.getenv(comp) for comp in ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]):
            # Components are set, let the validator assemble it
             pass # Pydantic validator will handle assembly
        
        logger.debug(f"Data prepared for Pydantic AppSettings initialization: {initial_data}")
        try:
            _settings_instance = AppSettings(**initial_data)
            logger.info("Application settings loaded successfully.")
            # Log sensitive info carefully
            if _settings_instance.DATABASE_URL:
                logger.debug(f"Final DATABASE_URL (sensitive part masked): {_settings_instance.DATABASE_URL.replace(_settings_instance.DB_PASSWORD, '********') if _settings_instance.DB_PASSWORD else _settings_instance.DATABASE_URL}")
        except Exception as e:
            logger.error(f"Error initializing AppSettings with Pydantic: {e}", exc_info=True)
            # Fallback to basic settings if Pydantic fails catastrophically
            _settings_instance = AppSettings() # Default values
            logger.warning("Falling back to default AppSettings due to initialization error.")

    return _settings_instance

# Example usage:
if __name__ == "__main__":
    settings = get_settings()
    print("App Name:", settings.APP_NAME)
    print("App Version:", settings.APP_VERSION)
    if settings.DATABASE_URL:
        print("Database URL (masked):", settings.DATABASE_URL.replace(settings.DB_PASSWORD, '********') if settings.DB_PASSWORD else settings.DATABASE_URL)
    else:
        print("Database URL: Not configured")
    print("Log Level:", settings.LOG_LEVEL)
    print("Crawler Settings Delay:", settings.CRAWLER.default_delay_seconds)
    print("Downloaded Files Path:", settings.OUTPUT_LOCATIONS.downloaded_files)
    print("Target Extensions:", settings.TARGET_FILE_EXTENSIONS)
    print("Base Dir:", settings.APP_BASE_DIR)
    print(f"Full project root for .env loading: {env_path}")
    print(f"Full project root for YAML config: {PROJECT_ROOT / 'config' / 'default_config.yml'}")

    # Test if DATABASE_URL is correctly assembled or used
    if not settings.DATABASE_URL:
         print("\nWARNING: DATABASE_URL is not configured. Database operations will fail.")
         print("Ensure DATABASE_URL is set in .env or individual DB_USER, DB_PASSWORD, etc. are set.")
    else:
        print(f"\nDATABASE_URL is set to: {settings.DATABASE_URL[:20]}...") # Print start to confirm
    
    if settings.DB_PASSWORD:
        print("DB_PASSWORD is set (should be masked in logs).")
    else:
        print("DB_PASSWORD is not set (or not loaded).")
