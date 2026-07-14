"""Batch processing logic for parallel row enrichment."""
import asyncio
import logging
import time
import sys
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BatchProgress:
    """Tracks progress of batch processing."""
    total: int
    completed: int = 0
    failed: int = 0
    start_time: float = field(default_factory=time.time)
    errors: List[str] = field(default_factory=list)

    def update(self, success: bool = True, error: str = ""):
        if success:
            self.completed += 1
        else:
            self.failed += 1
            if error:
                self.errors.append(error)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time

    @property
    def eta(self) -> str:
        if self.completed == 0:
            return "calculating..."
        rate = self.completed / self.elapsed
        remaining = (self.total - self.completed) / rate if rate > 0 else 0
        if remaining < 60:
            return f"{remaining:.0f}s"
        return f"{remaining / 60:.1f}m"

    def progress_bar(self, width: int = 40) -> str:
        """Render a progress bar string."""
        ratio = self.completed / self.total if self.total > 0 else 0
        filled = int(width * ratio)
        bar = "█" * filled + "░" * (width - filled)
        pct = ratio * 100
        return f"|{bar}| {self.completed}/{self.total} ({pct:.0f}%)"

    def __str__(self) -> str:
        bar = self.progress_bar()
        return f"{bar} | ETA: {self.eta} | Failed: {self.failed}"


async def process_batch(
    rows: List[Dict[str, Any]],
    enrichment_fn: Callable,
    batch_size: int = 10,
    max_concurrency: int = 5,
    show_progress: bool = True,
) -> List[Dict[str, Any]]:
    """Process rows in parallel batches with progress tracking."""
    progress = BatchProgress(total=len(rows))
    results = [None] * len(rows)
    semaphore = asyncio.Semaphore(max_concurrency)

    async def process_one(idx: int, row: Dict[str, Any]):
        async with semaphore:
            try:
                result = await enrichment_fn(row)
                results[idx] = result
                progress.update(success=True)
            except Exception as e:
                results[idx] = {**row, "_error": str(e)}
                progress.update(success=False, error=str(e))
        if show_progress and (progress.completed + progress.failed) % 10 == 0:
            logger.debug("Batch progress: %s", progress)

    # Create tasks for all rows
    tasks = [process_one(i, row) for i, row in enumerate(rows)]

    # Run in batches to control concurrency
    for i in range(0, len(tasks), max_concurrency):
        batch = tasks[i : i + max_concurrency]
        await asyncio.gather(*batch)
        if show_progress:
            logger.debug("Batch progress: %s", progress)

    if show_progress:
        logger.debug("Batch progress final: %s", progress)

    return results


def sync_process_batch(
    rows: List[Dict[str, Any]],
    enrichment_fn: Callable,
    batch_size: int = 10,
    show_progress: bool = True,
) -> List[Dict[str, Any]]:
    """Synchronous wrapper for batch processing."""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(
            process_batch(rows, enrichment_fn, batch_size, show_progress=show_progress)
        )
    finally:
        loop.close()
