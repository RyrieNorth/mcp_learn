import logging
import os
import sys
import json
import yaml

class JsonFormatter(logging.Formatter):
    """格式化日志为json

    Args:
        logging (json): json格式日志
    """
    def format(self, record):
        record_dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return json.dumps(record_dict, ensure_ascii=False)

class YamlFormatter(logging.Formatter):
    """格式化为yaml

    Args:
        logging (yaml): yaml格式日志
    """
    def format(self, record):
        record_dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        return yaml.dump(record_dict, allow_unicode=True).strip()

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

# Initialize global logger
logger = logging.getLogger("Kubernetes Resources Manager")
logger.setLevel(logging.INFO)  # Default level, can override

# Console output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(LogFormatter())

# Clean handlers and set only console by default
logger.handlers = []
logger.addHandler(console_handler)
logger.propagate = False

# === Extension functions ===
def set_log_level(level: str = "INFO"):
    """
    Dynamically set the log level.
    """
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

def set_log_file(file_name: str, file_path: str = None):
    """
    Enable file logging to a specified path and filename.
    """
    if file_path:
        os.makedirs(file_path, exist_ok=True)
        log_file = os.path.join(file_path, file_name)
    else:
        log_file = file_name
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(file_handler)

def set_log_format(format_type: str = "text"):
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            if format_type == "json":
                handler.setFormatter(JsonFormatter())
            elif format_type == "yaml":
                handler.setFormatter(YamlFormatter())
            else:
                handler.setFormatter(LogFormatter())