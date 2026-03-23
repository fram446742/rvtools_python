"""Logging configuration for RVTools"""

import logging
import sys
import io
from datetime import datetime


class DualStreamHandler(logging.Handler):
    """Handler that logs to both stdout and file with different levels per stream"""

    def __init__(self, file_path, console_level=logging.INFO):
        super().__init__()
        self.file_path = file_path
        self.file_handle = None
        self.console_level = console_level
        self._open_file()

    def _open_file(self):
        """Open file handle for writing"""
        try:
            self.file_handle = open(self.file_path, "a", buffering=1)  # Line buffering
        except Exception as e:
            print(f"Error opening log file: {e}", file=sys.stderr)

    def emit(self, record):
        """Emit a record to stdout (if level >= console_level) and to file (always)"""
        try:
            msg = self.format(record)

            # Print to stdout only if record level >= console_level (DEBUG messages hidden unless verbose)
            if record.levelno >= self.console_level:
                print(msg, flush=True)

            # Write to file with flush (always, including DEBUG)
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


def setup_logging(directory, verbose=False):
    """Setup logging to both stdout and file with proper buffering
    
    Args:
        directory: Directory to store log file
        verbose: If True, show INFO level in console. If False, show WARNING level.
                 File always contains DEBUG level.
    """
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

    # Set console level based on verbose flag
    # If verbose: show INFO and above
    # If not verbose: show WARNING and above (hide INFO and DEBUG)
    console_level = logging.INFO if verbose else logging.WARNING

    # Add dual handler with proper formatting
    handler = DualStreamHandler(log_file, console_level=console_level)
    handler.setLevel(logging.DEBUG)  # Handler accepts all, filter happens in emit()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Prevent propagation to root logger to avoid duplicates
    logger.propagate = False

    return logger, log_file
