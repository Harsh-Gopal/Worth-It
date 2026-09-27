import asyncio
import logging
from typing import Set, Dict, Any, Optional

from app.config import get_settings

log = logging.getLogger("scan_context")

class ScanBudgetExhausted(Exception):
    """Raised when the scan budget is exhausted."""
    pass

class ScanContext:
    """
    Tracks request budget, handles deduplication, and bounds concurrency for a single scan run.
    """
    def __init__(self):
        settings = get_settings()
        self.max_requests = settings.max_external_requests_per_scan
        self.max_locations = settings.max_locations_per_scan
        self.concurrency_limit = settings.max_concurrent_requests
        
        self.requests_made = 0
        self.locations_scanned = 0
        self.cache_hits = 0
        self.deduplicated_requests = 0
        
        self._semaphore = asyncio.Semaphore(self.concurrency_limit)
        self._in_flight: Dict[str, asyncio.Event] = {}
        self._completed: Set[str] = set()
        
    def check_budget(self):
        """Raises ScanBudgetExhausted if budget is exceeded."""
        if self.requests_made >= self.max_requests:
            log.warning("Scan request budget exhausted (%d requests)", self.max_requests)
            raise ScanBudgetExhausted("Max external requests reached")
        
        if self.locations_scanned >= self.max_locations:
            log.warning("Scan locations budget exhausted (%d locations)", self.max_locations)
            raise ScanBudgetExhausted("Max locations reached")

    async def execute_request(self, deduplication_key: str, coro: Any) -> Any:
        """
        Executes a coroutine with concurrency limits and deduplication.
        If deduplication_key is already in flight, waits for it but does not execute coro again.
        If it has been completed, skips it entirely (or retrieves from short-ttl cache if implemented inside coro).
        """
        if deduplication_key in self._completed:
            self.deduplicated_requests += 1
            return None # Or return from cache if needed, usually callers should check cache first.
            
        if deduplication_key in self._in_flight:
            self.deduplicated_requests += 1
            await self._in_flight[deduplication_key].wait()
            return None # The caller will likely hit the cache right after this returns.
            
        # We are the first to execute this
        event = asyncio.Event()
        self._in_flight[deduplication_key] = event
        
        try:
            self.check_budget()
            async with self._semaphore:
                self.check_budget() # Check again after acquiring semaphore
                self.requests_made += 1
                result = await coro
                
                self._completed.add(deduplication_key)
                return result
        finally:
            event.set()
            if deduplication_key in self._in_flight:
                del self._in_flight[deduplication_key]
