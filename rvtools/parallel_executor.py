"""Parallel execution of collectors using ThreadPoolExecutor"""
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger('rvtools')


class ParallelCollectorExecutor:
    """Execute collectors in parallel with specified number of threads"""

    def __init__(self, max_workers=None):
        """
        Initialize executor
        
        Args:
            max_workers: Number of threads. If None, uses min(8, cpu_count())
        """
        if max_workers is None:
            max_workers = min(8, os.cpu_count() or 4)
        
        self.max_workers = max_workers
        logger.info(f"Initialized parallel executor with {max_workers} workers")

    def execute_collectors(self, collectors, format_type='xlsx'):
        """
        Execute all collectors in parallel
        
        Args:
            collectors: List of collector instances
            format_type: Export format
            
        Returns:
            dict: {collector.sheet_name: data}
        """
        results = {}
        
        logger.info(f"Starting parallel collection with {self.max_workers} threads")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {
                executor.submit(self._run_collector, collector, format_type): collector
                for collector in collectors
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(futures):
                collector = futures[future]
                try:
                    data = future.result()
                    if data:
                        results[collector.sheet_name] = data
                        logger.info(f"✓ Completed: {collector.sheet_name}")
                    completed += 1
                except Exception as e:
                    logger.error(f"✗ Failed: {collector.sheet_name} - {e}")
                    completed += 1
            
            logger.info(f"Parallel collection completed: {completed}/{len(collectors)} sheets")
        
        return results

    def _run_collector(self, collector, format_type):
        """Run a single collector (executed in thread)"""
        try:
            return collector.run(format_type=format_type)
        except Exception as e:
            logger.error(f"Error in collector {collector.sheet_name}: {e}", exc_info=True)
            return []
