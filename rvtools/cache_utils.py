"""Performance optimization utilities for collectors"""

import logging

logger = logging.getLogger("rvtools")


class ViewCache:
    """Cache container views to avoid repeated API calls"""

    def __init__(self, content):
        """Initialize cache with vCenter content"""
        self.content = content
        self._cache = {}

    def get_view(self, container, view_types, recursive=True):
        """
        Get a container view, using cache if available

        Args:
            container: Container object (e.g., rootFolder)
            view_types: List of vim types to view
            recursive: Whether to search recursively

        Returns:
            Container view
        """
        # Create cache key from view types
        key = tuple(sorted([str(v) for v in view_types])) + (str(recursive),)

        if key not in self._cache:
            try:
                view = self.content.viewManager.CreateContainerView(
                    container, view_types, recursive
                )
                self._cache[key] = view
                logger.debug(f"Created container view for {view_types}")
            except Exception as e:
                logger.error(f"Failed to create container view: {e}")
                return None

        return self._cache.get(key)

    def get_list(self, view_types):
        """
        Get list of objects of given types

        Args:
            view_types: List of vim types

        Returns:
            List of objects
        """
        view = self.get_view(self.content.rootFolder, view_types)
        if view:
            return view.view
        return []

    def get_first(self, view_types):
        """Get first object of given types"""
        items = self.get_list(view_types)
        return items[0] if items else None

    def clear(self):
        """Clear cache"""
        self._cache.clear()
        logger.debug("Cleared view cache")


def get_parent_object(obj, parent_type):
    """
    Get parent object of specific type by traversing hierarchy

    Args:
        obj: Starting object
        parent_type: vim type to search for

    Returns:
        Parent object or None
    """
    try:
        current = obj
        max_iterations = 100  # Prevent infinite loops
        iterations = 0

        while current and iterations < max_iterations:
            if isinstance(current, parent_type):
                return current
            current = getattr(current, "parent", None)
            iterations += 1

        return None
    except Exception:
        return None
