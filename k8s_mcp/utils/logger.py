import logging
import sys

class LogFormatter(logging.Formatter):
    """
    Custom log formatter with ANSI color codes for console output.
    Each log level is assigned a distinct color to improve readability.
    """
    COLORS = {
        "DEBUG": "\033[37m",    # Gray
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[41m", # Red background
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        time_str = self.formatTime(record, self.datefmt)
        message = f"[{time_str}] [{record.levelname}] {record.getMessage()}"
        return f"{log_color}{message}{self.RESET}"


# Initialize the global logger
logger = logging.getLogger("llm_logger")
logger.setLevel(logging.DEBUG)  # Set to DEBUG/INFO/ERROR to control verbosity

# Configure console output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(LogFormatter())

# Replace default handlers with our custom one
logger.handlers = []
logger.addHandler(console_handler)
logger.propagate = False  # Prevent log messages from propagating to the root logger (avoids duplicate prints)
