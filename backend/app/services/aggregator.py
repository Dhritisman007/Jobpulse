"""Orchestrates all scrapers, runs deduplication, and stores results."""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, ScrapeLog
from app.scrapers.base import RawJob
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.remotive import RemotiveScraper
from app.scrapers.weworkremotely import WeWorkRemotelyScraper
from app.scrapers.arbeitnow import ArbeitnowScraper
from app.scrapers.jobicy import JobicyScraper
from app.services.deduplicator import Deduplicator

logger = logging.getLogger(__name__)

# All available scrapers
SCRAPERS = [
    RemoteOKScraper,
    RemotiveScraper,
    WeWorkRemotelyScraper,
    ArbeitnowScraper,
    JobicyScraper,
]


class Aggregator:
    """Orchestrates scraping from all sources, deduplicates, and stores jobs."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.deduplicator = Deduplicator(db)

    async def run_full_scrape(self) -> dict:
        """Run all scrapers concurrently and store results."""
        results = {
            "total_sources": len(SCRAPERS),
            "total_jobs_found": 0,
            "total_new_jobs": 0,
            "sources": [],
        }

        # Run all scrapers concurrently
        tasks = []
        for scraper_cls in SCRAPERS:
            tasks.append(self._run_single_scraper(scraper_cls))

        source_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in source_results:
            if isinstance(result, Exception):
                logger.error(f"Scraper failed: {result}")
                continue
            if result:
                results["sources"].append(result)
                results["total_jobs_found"] += result["jobs_found"]
                results["total_new_jobs"] += result["new_jobs"]

        return results

    async def _run_single_scraper(self, scraper_cls) -> dict:
        """Run a single scraper, deduplicate, and store results."""
        scraper = scraper_cls()
        source_name = scraper.source_name
        started_at = datetime.now(timezone.utc)

        # Create scrape log
        log = ScrapeLog(
            source=source_name,
            started_at=started_at,
            status="running",
        )
        self.db.add(log)
        await self.db.flush()

        try:
            # Fetch jobs
            raw_jobs = await scraper.fetch_jobs()
            jobs_found = len(raw_jobs)

            # Deduplicate and store
            new_jobs = 0
            for raw_job in raw_jobs:
                was_new = await self.deduplicator.process_job(raw_job)
                if was_new:
                    new_jobs += 1

            await self.db.commit()

            # Update log
            log.completed_at = datetime.now(timezone.utc)
            log.jobs_found = jobs_found
            log.new_jobs = new_jobs
            log.status = "completed"
            await self.db.commit()

            logger.info(
                f"[{source_name}] Completed: {jobs_found} found, {new_jobs} new"
            )

            return {
                "source": source_name,
                "status": "completed",
                "jobs_found": jobs_found,
                "new_jobs": new_jobs,
                "errors": "",
                "started_at": started_at.isoformat(),
                "completed_at": log.completed_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"[{source_name}] Error: {e}")
            log.completed_at = datetime.now(timezone.utc)
            log.errors = str(e)
            log.status = "failed"
            await self.db.commit()

            return {
                "source": source_name,
                "status": "failed",
                "jobs_found": 0,
                "new_jobs": 0,
                "errors": str(e),
                "started_at": started_at.isoformat(),
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            await scraper.close()

    async def run_single_source(self, source_name: str) -> dict:
        """Run a single scraper by source name."""
        for scraper_cls in SCRAPERS:
            if scraper_cls.source_name == source_name:
                return await self._run_single_scraper(scraper_cls)
        raise ValueError(f"Unknown source: {source_name}")
