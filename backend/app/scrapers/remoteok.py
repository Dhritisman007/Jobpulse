"""RemoteOK public API scraper — https://remoteok.com/api"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class RemoteOKScraper(BaseScraper):
    source_name = "remoteok"
    base_url = "https://remoteok.com/api"
    rate_limit_seconds = 3.0

    async def fetch_jobs(self) -> list[RawJob]:
        logger.info(f"[{self.source_name}] Fetching jobs...")
        response = await self._fetch_with_retry(self.base_url)
        if not response:
            return []

        try:
            data = response.json()
        except Exception as e:
            logger.error(f"[{self.source_name}] JSON parse error: {e}")
            return []

        # First element is metadata/legal notice, skip it
        listings = data[1:] if len(data) > 1 else data

        jobs = []
        for item in listings:
            try:
                job = self._parse_job(item)
                if job and job.is_fresher_friendly():
                    job.category = job.detect_category()
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Parse error: {e}")
                continue

        logger.info(f"[{self.source_name}] Found {len(jobs)} fresher-friendly jobs")
        return jobs

    def _parse_job(self, item: dict) -> Optional[RawJob]:
        """Parse a single RemoteOK job listing."""
        title = item.get("position", "").strip()
        company = item.get("company", "").strip()
        url = item.get("url", "")

        if not title or not company or not url:
            return None

        # Ensure full URL
        if url.startswith("/"):
            url = f"https://remoteok.com{url}"

        # Parse date
        posted_date = None
        date_str = item.get("date", "")
        if date_str:
            try:
                posted_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Build tags from the tags array
        tags = item.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        # Extract location
        location = item.get("location", "Remote") or "Remote"

        # Salary
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")
        salary_range = None
        if salary_min and salary_max:
            salary_range = f"${int(salary_min):,} - ${int(salary_max):,}"
        elif salary_min:
            salary_range = f"${int(salary_min):,}+"

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
