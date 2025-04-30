import logging
import sys


class LogFormatter(logging.Formatter):
    # 日志格式（带颜色）
    COLORS = {
        "DEBUG": "\033[37m",  # 灰色
        "INFO": "\033[32m",  # 绿色
        "WARNING": "\033[33m",  # 黄色
        "ERROR": "\033[31m",  # 红色
        "CRITICAL": "\033[41m",  # 红底
    }
    RESET = "\033[0m"

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        time_str = self.formatTime(record, self.datefmt)
        message = f"[{time_str}] [{record.levelname}] {record.getMessage()}"
        return f"{log_color}{message}{self.RESET}"


# 初始化 logger
logger = logging.getLogger("vm_logger")
logger.setLevel(logging.DEBUG)  # 可改为 INFO/ERROR 控制输出等级

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(LogFormatter())

logger.handlers = []
logger.addHandler(console_handler)
logger.propagate = False  # 不向上传播，避免重复打印
