"""Multi-strategy deduplication engine for cross-source job listings."""

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job
from app.scrapers.base import RawJob

logger = logging.getLogger(__name__)


class Deduplicator:
    """Deduplicates job listings using fingerprinting and URL matching."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_job(self, raw_job: RawJob) -> bool:
        """
        Check if job already exists, insert if new.
        Returns True if the job was newly inserted, False if duplicate.
        """
        fingerprint = raw_job.compute_fingerprint()

        # Strategy 1: Check fingerprint (company + title hash)
        existing = await self._find_by_fingerprint(fingerprint)
        if existing:
            logger.debug(f"Duplicate (fingerprint): {raw_job.title} @ {raw_job.company}")
            return False

        # Strategy 2: Check URL
        existing = await self._find_by_url(raw_job.url)
        if existing:
            logger.debug(f"Duplicate (URL): {raw_job.url}")
            return False

        # New job — insert
        job = Job(
            external_id=raw_job.external_id,
            source=raw_job.source,
            title=raw_job.title,
            company=raw_job.company,
            location=raw_job.location,
            description=raw_job.description,
            url=raw_job.url,
            posted_date=raw_job.posted_date,
            tags=raw_job.tags,
            salary_range=raw_job.salary_range,
            is_remote=raw_job.is_remote,
            category=raw_job.category,
            fingerprint=fingerprint,
        )
        self.db.add(job)
        try:
            await self.db.flush()
            logger.debug(f"New job: {raw_job.title} @ {raw_job.company}")
            return True
        except Exception as e:
            # Handle race condition on unique constraint
            await self.db.rollback()
            logger.debug(f"Duplicate (constraint): {raw_job.title} — {e}")
            return False

    async def _find_by_fingerprint(self, fingerprint: str) -> Optional[Job]:
        """Look up job by fingerprint hash."""
        result = await self.db.execute(
            select(Job).where(Job.fingerprint == fingerprint)
        )
        return result.scalar_one_or_none()

    async def _find_by_url(self, url: str) -> Optional[Job]:
        """Look up job by exact URL match."""
        result = await self.db.execute(
            select(Job).where(Job.url == url)
        )
        return result.scalar_one_or_none()
