"""Arbeitnow public API scraper — https://www.arbeitnow.com/api/job-board-api"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class ArbeitnowScraper(BaseScraper):
    source_name = "arbeitnow"
    base_url = "https://www.arbeitnow.com/api/job-board-api"
    rate_limit_seconds = 3.0

    async def fetch_jobs(self) -> list[RawJob]:
        logger.info(f"[{self.source_name}] Fetching jobs...")
        all_jobs = []
        page = 1
        max_pages = 3  # Limit to avoid excessive requests

        while page <= max_pages:
            response = await self._fetch_with_retry(
                self.base_url,
                params={"page": page}
            )
            if not response:
                break

            try:
                data = response.json()
                listings = data.get("data", [])
            except Exception as e:
                logger.error(f"[{self.source_name}] JSON parse error: {e}")
                break

            if not listings:
                break

            for item in listings:
                try:
                    job = self._parse_job(item)
                    if job and job.is_remote and job.is_fresher_friendly():
                        job.category = job.detect_category()
                        all_jobs.append(job)
                except Exception as e:
                    logger.warning(f"[{self.source_name}] Parse error: {e}")
                    continue

            # Check if there's a next page
            if not data.get("links", {}).get("next"):
                break
            page += 1

        logger.info(f"[{self.source_name}] Found {len(all_jobs)} fresher-friendly remote jobs")
        return all_jobs

    def _parse_job(self, item: dict) -> Optional[RawJob]:
        """Parse a single Arbeitnow job listing."""
        title = item.get("title", "").strip()
        company = item.get("company_name", "").strip()
        url = item.get("url", "")
        slug = item.get("slug", "")

        if not title or not company:
            return None

        # Build URL
        if not url and slug:
            url = f"https://www.arbeitnow.com/view/{slug}"
        if not url:
            return None

        # Check if remote
        is_remote = item.get("remote", False)
        location = item.get("location", "")
        if not location:
            location = "Remote" if is_remote else "On-site"

        # Parse date
        posted_date = None
        created_at = item.get("created_at")
        if created_at:
            try:
                if isinstance(created_at, (int, float)):
                    posted_date = datetime.fromtimestamp(created_at, tz=timezone.utc)
                else:
                    posted_date = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
            except (ValueError, TypeError, OSError):
                pass

        # Tags
        tags = item.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]

        # Description
        description = self._clean_html(item.get("description", ""))

        return RawJob(
            external_id=slug or str(item.get("id", "")),
            source=self.source_name,
            title=title,
            company=company,
            location=location,
            description=description,
            url=url,
            posted_date=posted_date,
            tags=tags,
            is_remote=is_remote,
        )
