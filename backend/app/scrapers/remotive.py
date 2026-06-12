"""Remotive public API scraper — https://remotive.com/api/remote-jobs"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


# Remotive category slugs relevant to our target roles
REMOTIVE_CATEGORIES = [
    "software-dev",
    "data",
    "devops",
    "finance",
]


class RemotiveScraper(BaseScraper):
    source_name = "remotive"
    base_url = "https://remotive.com/api/remote-jobs"
    # Remotive allows max 4 requests/day — be very conservative
    rate_limit_seconds = 10.0

    async def fetch_jobs(self) -> list[RawJob]:
        logger.info(f"[{self.source_name}] Fetching jobs...")
        all_jobs = []

        for category in REMOTIVE_CATEGORIES:
            response = await self._fetch_with_retry(
                self.base_url,
                params={"category": category, "limit": 50}
            )
            if not response:
                continue

            try:
                data = response.json()
                listings = data.get("jobs", [])
            except Exception as e:
                logger.error(f"[{self.source_name}] JSON parse error: {e}")
                continue

            for item in listings:
                try:
                    job = self._parse_job(item)
                    if job and job.is_fresher_friendly():
                        job.category = job.detect_category()
                        all_jobs.append(job)
                except Exception as e:
                    logger.warning(f"[{self.source_name}] Parse error: {e}")
                    continue

        logger.info(f"[{self.source_name}] Found {len(all_jobs)} fresher-friendly jobs")
        return all_jobs

    def _parse_job(self, item: dict) -> Optional[RawJob]:
        """Parse a single Remotive job listing."""
        title = item.get("title", "").strip()
        company = item.get("company_name", "").strip()
        url = item.get("url", "")

        if not title or not company or not url:
            return None

        # Parse date
        posted_date = None
        date_str = item.get("publication_date", "")
        if date_str:
            try:
                posted_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    posted_date = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S")
                    posted_date = posted_date.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

        # Tags from category
        tags = []
        category = item.get("category", "")
        if category:
            tags.append(category)
        job_tags = item.get("tags", [])
        if isinstance(job_tags, list):
            tags.extend(job_tags)

        # Location
        location = item.get("candidate_required_location", "Remote") or "Remote"

        # Salary
        salary_range = item.get("salary", None) or None

        # Description
        description = self._clean_html(item.get("description", ""))

        return RawJob(
            external_id=str(item.get("id", "")),
            source=self.source_name,
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            posted_date=posted_date,
            tags=tags,
            salary_range=salary_range,
            is_remote=True,
        )
