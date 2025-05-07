# This file makes Python treat the `breachwatch` directory as a package.
# You can put package-level initialization code here if needed.

import logging
from breachwatch.utils.logger import setup_logging
from breachwatch.utils.config_loader import get_settings

# Setup logging as soon as the package is imported
settings = get_settings()
setup_logging(level=settings.LOG_LEVEL)

logger = logging.getLogger(__name__)
logger.info(f"BreachWatch Backend package initialized. Log level: {settings.LOG_LEVEL}")
