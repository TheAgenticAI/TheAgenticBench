import logging
import os

from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger

# Load environment variables from a .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Custom formatter for colored logs
class CustomFormatter(logging.Formatter):

    grey = "\x1b[38;20m"
    blue = "\x1b[34;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "[%(asctime)s] %(levelname)s {%(filename)s:%(lineno)d} - %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Custom function to configure the logger
def configure_logger(level: str = "INFO") -> None:
    """
    Configures the logger based on the given level and log format.

    Parameters:
    - level (str): The log level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
                   This value can now be set using the `LOG_LEVEL` environment variable.
    """
    level = os.getenv("LOG_LEVEL", level).upper()  # Use environment variable or default to 'INFO'
    log_format = os.getenv("LOG_MESSAGES_FORMAT", "text").lower()


    # Get the root logger
    logger = logging.getLogger()
    
    # Remove all handlers to avoid duplicate logging
    for handler in logger.handlers:
        logger.removeHandler(handler)

    logger.setLevel(level)
    handler = logging.StreamHandler()

   # Decide format based on LOG_MESSAGES_FORMAT env variable
    if log_format == "json":
        # JSON-based logging format
        formatter = jsonlogger.JsonFormatter(
            fmt='%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Use custom colored formatter for text
        formatter = CustomFormatter()

    handler.setFormatter(formatter)
    logger.handlers = []  # Clear existing handlers
    logger.addHandler(handler)

    # Ensure other loggers have the same handler
    http_loggers = ["openai", "autogen"]
    for http_logger in http_loggers:
        lib_logger = logging.getLogger(http_logger)
        lib_logger.setLevel(logging.INFO)
        lib_logger.handlers = []  # Clear any existing handlers
        lib_logger.addHandler(handler)  # Add the same handler


# Call the configure logger function to set up the logger initially
configure_logger()

# Function to set log level
def set_log_level(level: str) -> None:
    """
    Set the log level for the logger.

    Parameters:
    - level (str): A logging level such as 'debug', 'info', 'warning', 'error', or 'critical'.
    """
    configure_logger(level)

# Set default log levels for other libraries
# logging.getLogger("httpcore").setLevel(logging.DEBUG)
# logging.getLogger("httpx").setLevel(logging.DEBUG)
# logging.getLogger("openai").setLevel(logging.DEBUG)
# logging.getLogger("autogen").setLevel(logging.DEBUG)
logging.getLogger("matplotlib.pyplot").setLevel(logging.WARNING)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
logging.getLogger("PIL.Image").setLevel(logging.WARNING)

# Re-export the logger for ease of use
__all__ = ["logger", "set_log_level"]