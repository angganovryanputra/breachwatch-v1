import logging
import sys

def setup_logging(level: str = "INFO", service_name: str = "BreachWatchBackend"):
    """
    Sets up structured logging for the application.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers to avoid duplicate logs if setup_logging is called multiple times
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create a handler for stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)

    # Create a formatter
    # Example format: 2023-10-27 10:00:00,123 - BreachWatchBackend - INFO - module_name - Log message
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S,%03d"
    )
    stream_handler.setFormatter(formatter)

    # Add the handler to the root logger
    root_logger.addHandler(stream_handler)

    # Suppress verbose logging from some libraries if needed
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING) # Quieten Uvicorn access logs unless error
    logging.getLogger("httpx").setLevel(logging.WARNING) # Quieten httpx info logs
    logging.getLogger("httpcore").setLevel(logging.WARNING) # Quieten httpcore logs


    # Test log message
    # logging.getLogger(service_name).info(f"Logging setup complete. Log level: {level}")

if __name__ == "__main__":
    setup_logging(level="DEBUG")
    
    logger = logging.getLogger("TestLogger")
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")

    # Test httpx and uvicorn suppression (won't show if not run under uvicorn)
    logging.getLogger("httpx").info("This httpx info log should be suppressed.")
    logging.getLogger("uvicorn.access").info("This uvicorn access log should be suppressed.")
    logging.getLogger("uvicorn.access").error("This uvicorn error log should appear.")
