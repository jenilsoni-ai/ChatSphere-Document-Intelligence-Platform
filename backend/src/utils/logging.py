import logging
import sys
import os
from typing import Optional

# Configure the root logger
def configure_logging(log_level: str = "INFO"):
    """
    Configure the root logger with the specified log level.
    
    Args:
        log_level: The log level to use. Default is INFO.
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure the root logger
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stdout
    )

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: The name of the logger. If None, the calling module's name will be used.
    
    Returns:
        A configured logger instance.
    """
    if name is None:
        # Get the name of the calling module
        import inspect
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else "unknown"
    
    # Get or create a logger with the specified name
    logger = logging.getLogger(name)
    
    # Ensure we have at least one handler
    if not logger.handlers:
        # Add a console handler if none exists
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def setup_file_logging(log_dir: str = "logs", filename: str = "app.log"):
    """
    Set up file logging in addition to console logging.
    
    Args:
        log_dir: The directory to store log files in. Default is 'logs'.
        filename: The name of the log file. Default is 'app.log'.
    """
    # Create the log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Create a file handler for logging
    log_path = os.path.join(log_dir, filename)
    file_handler = logging.FileHandler(log_path)
    
    # Set the formatter for the file handler
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    
    # Add the file handler to the root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    # Log that file logging has been set up
    root_logger.info(f"File logging set up at {log_path}")

# Configure the root logger with default settings
configure_logging(os.environ.get("LOG_LEVEL", "INFO")) 