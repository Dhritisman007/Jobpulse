"""Jobicy public API scraper — https://jobicy.com/api/v2/remote-jobs"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.scrapers.base import BaseScraper, RawJob

logger = logging.getLogger(__name__)


class JobicyScraper(BaseScraper):
    source_name = "jobicy"
    base_url = "https://jobicy.com/api/v2/remote-jobs"
    rate_limit_seconds = 5.0

    async def fetch_jobs(self) -> list[RawJob]:
        logger.info(f"[{self.source_name}] Fetching jobs...")

        response = await self._fetch_with_retry(
            self.base_url,
            params={
                "count": 50,
                "geo": "anywhere",
                "industry": "tech",
                "tag": "software development",
            }
        )
        if not response:
            return []

        try:
            data = response.json()
            listings = data.get("jobs", [])
        except Exception as e:
            logger.error(f"[{self.source_name}] JSON parse error: {e}")
            return []

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
        """Parse a single Jobicy job listing."""
        title = item.get("jobTitle", "").strip()
        company = item.get("companyName", "").strip()
        url = item.get("url", "")

        if not title or not company or not url:
            return None

        # Parse date
        posted_date = None
        pub_date = item.get("pubDate", "")
        if pub_date:
            try:
                posted_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                try:
                    posted_date = datetime.strptime(pub_date, "%Y-%m-%d %H:%M:%S")
                    posted_date = posted_date.replace(tzinfo=timezone.utc)
                except (ValueError, TypeError):
                    pass

        # Location
        location = item.get("jobGeo", "Remote") or "Remote"

        # Tags / job type
        tags = []
        job_type = item.get("jobType", "")
        if job_type:
            tags.extend(job_type if isinstance(job_type, list) else [job_type])
        job_industry = item.get("jobIndustry", "")
        if job_industry:
            tags.extend(job_industry if isinstance(job_industry, list) else [job_industry])

        # Salary
        salary_range = None
        sal_min = item.get("annualSalaryMin")
        sal_max = item.get("annualSalaryMax")
        sal_currency = item.get("salaryCurrency", "USD")
        if sal_min and sal_max:
            salary_range = f"{sal_currency} {sal_min} - {sal_max}"
        elif sal_min:
            salary_range = f"{sal_currency} {sal_min}+"

        # Description
        description = self._clean_html(item.get("jobDescription", ""))

        # Company logo (not used in RawJob, but could be)
        # logo = item.get("companyLogo", "")

        return RawJob(
            external_id=str(item.get("id", url)),
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
