"""Logging configuration for RVTools"""
import logging
import sys
from datetime import datetime


class DualStreamHandler(logging.Handler):
    """Handler that logs to both stdout and file"""

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def emit(self, record):
        """Emit a record"""
        msg = self.format(record)
        
        # Print to stdout
        print(msg)
        
        # Also write to file
        try:
            with open(self.file_path, 'a') as f:
                f.write(msg + '\n')
        except Exception:
            pass


def setup_logging(directory):
    """Setup logging to both stdout and file"""
    log_file = f"{directory}/rvtools_{datetime.now().strftime('%Y-%m-%d_%H.%M')}.log"
    
    # Ensure file exists
    with open(log_file, 'w') as f:
        f.write(f"RVTools Log - {datetime.now()}\n")
    
    logger = logging.getLogger('rvtools')
    logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers
    logger.handlers = []
    
    # Add dual handler
    handler = DualStreamHandler(log_file)
    handler.setLevel(logging.DEBUG)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger, log_file
