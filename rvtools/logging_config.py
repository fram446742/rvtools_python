"""Logging configuration for RVTools"""

import logging
import sys
import io
from datetime import datetime


class DualStreamHandler(logging.Handler):
    """Handler that logs to both stdout and file with proper buffering"""

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.file_handle = None
        self._open_file()

    def _open_file(self):
        """Open file handle for writing"""
        try:
            self.file_handle = open(self.file_path, "a", buffering=1)  # Line buffering
        except Exception as e:
            print(f"Error opening log file: {e}", file=sys.stderr)

    def emit(self, record):
        """Emit a record to both stdout and file"""
        try:
            msg = self.format(record)

            # Print to stdout with flush
            print(msg, flush=True)

            # Write to file with flush
            if self.file_handle and not self.file_handle.closed:
                self.file_handle.write(msg + "\n")
                self.file_handle.flush()
        except Exception as e:
            # Print to stderr if logging fails
            print(f"Error in logging handler: {e}", file=sys.stderr)

    def close(self):
        """Close file handle"""
        if self.file_handle and not self.file_handle.closed:
            self.file_handle.flush()
            self.file_handle.close()
        super().close()


def setup_logging(directory):
    """Setup logging to both stdout and file with proper buffering"""
    log_file = f"{directory}/rvtools_{datetime.now().strftime('%Y-%m-%d_%H.%M')}.log"

    # Initialize file with header
    try:
        with open(log_file, "w") as f:
            f.write(f"RVTools Log - {datetime.now()}\n")
            f.write("=" * 80 + "\n")
            f.flush()
    except Exception as e:
        print(f"Error creating log file: {e}", file=sys.stderr)

    logger = logging.getLogger("rvtools")
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(handler)

    # Add dual handler with proper formatting
    handler = DualStreamHandler(log_file)
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicates
    logger.propagate = False

    return logger, log_file
