"""VM annotation/custom field extraction utility"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger("rvtools")


class AnnotationExtractor:
    """Extract custom fields and annotations from VM objects"""

    @staticmethod
    def extract_vm_annotations(
        vm,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Extract VM custom fields/annotations with pattern matching.

        Args:
            vm: pyVmomi VM object
            include_patterns: List of glob patterns to include (e.g., ['com.emc.*', 'user-*'])
            exclude_patterns: List of glob patterns to exclude

        Returns:
            Dictionary of {key: value} for matching fields
        """
        result = {}

        try:
            # Try to extract from customValue if available
            if hasattr(vm, 'customValue') and vm.customValue:
                for field in vm.customValue:
                    try:
                        key = field.key
                        value = field.value
                        if AnnotationExtractor._matches_patterns(key, include_patterns, exclude_patterns):
                            result[key] = str(value) if value else ""
                    except Exception as e:
                        logger.debug(f"Error extracting custom field: {e}")
                        continue

            # Try to extract from config.annotation
            if hasattr(vm, 'config') and hasattr(vm.config, 'annotation'):
                annotation = vm.config.annotation
                if annotation and isinstance(annotation, str):
                    # Parse annotation as key=value pairs (common format)
                    for line in annotation.split('\n'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            if AnnotationExtractor._matches_patterns(key, include_patterns, exclude_patterns):
                                result[key] = value.strip()
        except Exception as e:
            logger.warning(f"Error extracting VM annotations: {e}")

        return result

    @staticmethod
    def _matches_patterns(
        key: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> bool:
        """
        Check if key matches include patterns and not exclude patterns.

        Supports glob-style patterns:
        - * matches any characters
        - ? matches single character
        - [abc] matches a, b, or c
        """
        # If include patterns provided, key must match at least one
        if include_patterns:
            if not any(AnnotationExtractor._glob_match(key, pattern) for pattern in include_patterns):
                return False

        # If exclude patterns provided, key must not match any
        if exclude_patterns:
            if any(AnnotationExtractor._glob_match(key, pattern) for pattern in exclude_patterns):
                return False

        return True

    @staticmethod
    def _glob_match(text: str, pattern: str) -> bool:
        """Simple glob pattern matching"""
        # Convert glob pattern to regex
        regex_pattern = "^" + pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".") + "$"
        return bool(re.match(regex_pattern, text))
