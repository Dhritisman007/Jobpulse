"""Pydantic schemas for API request/response serialization."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


# ─── Job Schemas ───

class JobBase(BaseModel):
    title: str
    company: str
    location: str = "Remote"
    description: str = ""
    url: str
    posted_date: Optional[datetime] = None
    tags: list[str] = []
    salary_range: Optional[str] = None
    is_remote: bool = True
    category: str = "other"


class JobCreate(JobBase):
    """Used for manual job import."""
    source: str = "manual"


class JobResponse(JobBase):
    id: int
    source: str
    external_id: Optional[str] = None
    scraped_at: datetime
    match_score: Optional[float] = None
    keyword_hits: list[str] = []
    application_status: Optional[str] = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    page: int = 1
    per_page: int = 30


# ─── Application Schemas ───

class ApplicationUpdate(BaseModel):
    status: str  # interested, applied, skipped, rejected, interview, offer
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: int
    status: str
    applied_date: Optional[datetime] = None
    notes: str = ""
    cover_letter_text: str = ""
    created_at: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None

    model_config = {"from_attributes": True}


# ─── Cover Letter Schemas ───

class CoverLetterRequest(BaseModel):
    job_id: int


class CoverLetterResponse(BaseModel):
    job_id: int
    cover_letter: str
    generated_at: datetime


# ─── Scrape Schemas ───

class ScrapeStatus(BaseModel):
    source: str
    status: str
    jobs_found: int = 0
    new_jobs: int = 0
    errors: str = ""
    started_at: datetime
    completed_at: Optional[datetime] = None


class ScrapeResult(BaseModel):
    total_sources: int
    total_jobs_found: int
    total_new_jobs: int
    sources: list[ScrapeStatus]


# ─── Filter Schemas ───

class JobFilter(BaseModel):
    category: Optional[str] = None
    source: Optional[str] = None
    status: Optional[str] = None
    min_score: Optional[float] = None
    search: Optional[str] = None
    days_ago: Optional[int] = 7
    sort_by: str = "match_score"  # match_score, posted_date, company
    sort_order: str = "desc"  # asc, desc
    page: int = 1
    per_page: int = 30


# ─── Resume Schema ───

class ResumeData(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    summary: str = ""
    skills: list[str] = []
    frameworks: list[str] = []
    languages: list[str] = []
    tools: list[str] = []
    experience: list[dict] = []
    education: list[dict] = []
    projects: list[dict] = []
    certifications: list[str] = []
    target_roles: list[str] = [
        "Full-Stack Developer",
        "Machine Learning Engineer",
        "Data Scientist",
        "FinTech Developer",
        "Blockchain Developer",
        "Data Analyst",
    ]


# ─── Manual Import ───

class ManualJobImport(BaseModel):
    url: str
    title: Optional[str] = None
    company: Optional[str] = None
    description: Optional[str] = None
    source: str = "manual"
