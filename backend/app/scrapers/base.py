"""Abstract base scraper with shared logic for all job sources."""

import asyncio
import hashlib
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


# Keywords that signal fresher/entry-level positions
FRESHER_KEYWORDS = [
    "intern", "internship", "junior", "entry-level", "entry level",
    "fresher", "associate", "trainee", "graduate", "new grad",
    "early career", "apprentice", "co-op", "student",
]

# Keywords for role categories
CATEGORY_KEYWORDS = {
    "fullstack": [
        "full-stack", "fullstack", "full stack", "frontend", "backend",
        "react", "next.js", "nextjs", "vue", "angular", "node", "fastapi",
        "django", "flask", "express", "typescript", "javascript",
        "web developer", "software engineer", "software developer",
    ],
    "ml_ds": [
        "machine learning", "ml engineer", "data science", "data scientist",
        "deep learning", "nlp", "natural language", "computer vision",
        "pytorch", "tensorflow", "ai engineer", "artificial intelligence",
        "llm", "generative ai", "mlops", "model training",
    ],
    "fintech": [
        "fintech", "quantitative", "quant", "trading", "algorithmic",
        "financial", "finance", "banking", "payments", "blockchain",
        "defi", "cryptocurrency", "risk analysis", "portfolio",
    ],
    "blockchain": [
        "blockchain", "web3", "smart contract", "solidity", "ethereum",
        "defi", "nft", "crypto", "decentralized", "dapp", "rust",
        "substrate", "cosmos", "polygon",
    ],
    "data_analysis": [
        "data analyst", "data analysis", "business analyst", "bi analyst",
        "analytics", "sql", "tableau", "power bi", "excel", "reporting",
        "data visualization", "dashboard", "etl", "data engineering",
    ],
}


@dataclass
class RawJob:
    """Normalized job listing from any source."""
    external_id: str = ""
    source: str = ""
    title: str = ""
    company: str = ""
    location: str = "Remote"
    description: str = ""
    url: str = ""
    posted_date: Optional[datetime] = None
    tags: list[str] = field(default_factory=list)
    salary_range: Optional[str] = None
    is_remote: bool = True
    category: str = "other"

    def compute_fingerprint(self) -> str:
        """Generate a deduplication fingerprint from company + title + url domain."""
        title_norm = re.sub(r'[^a-z0-9\s]', '', self.title.lower()).strip()
        company_norm = re.sub(r'[^a-z0-9\s]', '', self.company.lower()).strip()
        raw = f"{company_norm}|{title_norm}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def detect_category(self) -> str:
        """Auto-detect job category from title + description."""
        text = f"{self.title} {self.description}".lower()
        scores = {}
        for cat, keywords in CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scores[cat] = score
        if scores:
            return max(scores, key=scores.get)
        return "other"

    def is_fresher_friendly(self) -> bool:
        """Check if the job appears suitable for freshers."""
        text = f"{self.title} {self.description}".lower()
        # Positive signals
        if any(kw in text for kw in FRESHER_KEYWORDS):
            return True
        # Negative signals — skip if explicitly requires 3+ years
        exp_pattern = r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of)?\s*(?:experience|exp)'
        matches = re.findall(exp_pattern, text)
        if matches:
            min_exp = min(int(m) for m in matches)
            return min_exp <= 2
        # If no experience mentioned, likely open
        return True


class BaseScraper(ABC):
    """Base class for all job source scrapers."""

    source_name: str = "unknown"
    base_url: str = ""
    rate_limit_seconds: float = 2.0  # Min seconds between requests

    def __init__(self):
        self._last_request_time = 0
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "User-Agent": "RemoteJobSearchBot/1.0 (personal-project; contact@example.com)",
                    "Accept": "application/json",
                },
                follow_redirects=True,
            )
        return self._client

    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        now = asyncio.get_event_loop().time()
        elapsed = now - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            await asyncio.sleep(self.rate_limit_seconds - elapsed)
        self._last_request_time = asyncio.get_event_loop().time()

    async def _fetch_with_retry(self, url: str, params: dict = None, max_retries: int = 3) -> Optional[httpx.Response]:
        """Fetch URL with retry logic and exponential backoff."""
        client = await self._get_client()
        for attempt in range(max_retries):
            try:
                await self._rate_limit()
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait = 2 ** (attempt + 2)
                    logger.warning(f"[{self.source_name}] Rate limited, waiting {wait}s...")
                    await asyncio.sleep(wait)
                elif e.response.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning(f"[{self.source_name}] Server error {e.response.status_code}, retry in {wait}s")
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"[{self.source_name}] HTTP {e.response.status_code}: {e}")
                    return None
            except httpx.RequestError as e:
                wait = 2 ** attempt
                logger.warning(f"[{self.source_name}] Request error: {e}, retry in {wait}s")
                await asyncio.sleep(wait)
        logger.error(f"[{self.source_name}] Failed after {max_retries} retries: {url}")
        return None

    @abstractmethod
    async def fetch_jobs(self) -> list[RawJob]:
        """Fetch job listings from the source. Must be implemented by subclasses."""
        ...

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _clean_html(self, html: str) -> str:
        """Strip HTML tags from a string."""
        if not html:
            return ""
        clean = re.sub(r'<[^>]+>', ' ', html)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:5000]  # Cap description length
