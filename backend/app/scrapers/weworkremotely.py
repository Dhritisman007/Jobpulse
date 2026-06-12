"""We Work Remotely RSS feed scraper — https://weworkremotely.com/remote-jobs.rss"""

import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)

# WWR category RSS feeds
WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-data-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
    "https://weworkremotely.com/remote-jobs.rss",
]


class WeWorkRemotelyScraper(BaseScraper):
    source_name = "weworkremotely"
    base_url = "https://weworkremotely.com"
    rate_limit_seconds = 5.0

    async def fetch_jobs(self) -> list[RawJob]:
        logger.info(f"[{self.source_name}] Fetching RSS feeds...")
        all_jobs = []
        seen_urls = set()

        for feed_url in WWR_FEEDS:
            response = await self._fetch_with_retry(feed_url)
            if not response:
                continue

            try:
                feed = feedparser.parse(response.text)
            except Exception as e:
                logger.error(f"[{self.source_name}] RSS parse error: {e}")
                continue

            for entry in feed.entries:
                try:
                    job = self._parse_entry(entry)
                    if job and job.url not in seen_urls and job.is_fresher_friendly():
                        job.category = job.detect_category()
                        all_jobs.append(job)
                        seen_urls.add(job.url)
                except Exception as e:
                    logger.warning(f"[{self.source_name}] Parse error: {e}")
                    continue

        logger.info(f"[{self.source_name}] Found {len(all_jobs)} fresher-friendly jobs")
        return all_jobs

    def _parse_entry(self, entry) -> Optional[RawJob]:
        """Parse a single RSS feed entry."""
        title_raw = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()

        if not title_raw or not link:
            return None

        # WWR titles are often "Company: Job Title"
        if ":" in title_raw:
            parts = title_raw.split(":", 1)
            company = parts[0].strip()
            title = parts[1].strip()
        else:
            company = "Unknown"
            title = title_raw

        # Parse publication date
        posted_date = None
        pub_date = getattr(entry, "published", None)
        if pub_date:
            try:
                posted_date = parsedate_to_datetime(pub_date)
                if posted_date.tzinfo is None:
                    posted_date = posted_date.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Description from summary/content
        description = ""
        if hasattr(entry, "summary"):
            description = self._clean_html(entry.summary)
        elif hasattr(entry, "content") and entry.content:
            description = self._clean_html(entry.content[0].get("value", ""))

        # Tags from categories
        tags = []
        if hasattr(entry, "tags"):
            tags = [t.get("term", "") for t in entry.tags if t.get("term")]

        return RawJob(
            external_id=link,
            source=self.source_name,
            title=title,
            company=company,
            location="Remote",
            description=description,
            url=link,
            posted_date=posted_date,
            tags=tags,
            is_remote=True,
        )
