"""Base class for all data collectors"""

from abc import ABC, abstractmethod
import logging
from rvtools.cache_utils import ViewCache

logger = logging.getLogger("rvtools")

# Global view cache shared across all collectors
_global_view_cache = None


def set_global_view_cache(cache):
    """Set the global view cache for all collectors"""
    global _global_view_cache
    _global_view_cache = cache


def get_global_view_cache():
    """Get the global view cache"""
    return _global_view_cache


class BaseCollector(ABC):
    """Abstract base class for collecting vCenter data"""

    def __init__(self, service_instance, directory):
        """
        Initialize collector with vCenter connection and output directory

        Args:
            service_instance: pyVmomi service instance connected to vCenter
            directory: Output directory for exports
        """
        self.service_instance = service_instance
        self.directory = directory
        try:
            self.content = service_instance.RetrieveContent()
        except Exception as e:
            logger.error(f"Failed to retrieve content: {e}")
            self.content = None

        # Use global cache if available, otherwise create local one
        if _global_view_cache is not None:
            self.view_cache = _global_view_cache
        else:
            self.view_cache = ViewCache(self.content) if self.content else None

    @property
    @abstractmethod
    def sheet_name(self):
        """Name of the sheet (e.g., 'vInfo', 'vHealth')"""
        pass

    @abstractmethod
    def collect(self):
        """
        Collect data from vCenter

        Returns:
            list: List of dictionaries containing collected data
        """
        pass

    def run(self, format_type="xlsx"):
        """
        Run collector and return data

        Args:
            format_type: Ignored (for compatibility). Data is always returned.

        Returns:
            list: List of dictionaries containing collected data
        """
        try:
            logger.debug(f"## Processing {self.sheet_name} module")
            data = self.collect()

            if not data:
                logger.warning(f"No data collected for {self.sheet_name}")
                return []

            return data
        except Exception as e:
            logger.error(f"Error processing {self.sheet_name}: {e}", exc_info=True)
            return []
