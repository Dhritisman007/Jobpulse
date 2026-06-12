"""SQLAlchemy ORM models for jobs, scores, applications, and scrape logs."""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, Enum, ForeignKey, Boolean, JSON
)
from sqlalchemy.orm import relationship

from app.database import Base


class ApplicationStatus(str, enum.Enum):
    INTERESTED = "interested"
    APPLIED = "applied"
    SKIPPED = "skipped"
    REJECTED = "rejected"
    INTERVIEW = "interview"
    OFFER = "offer"


class JobCategory(str, enum.Enum):
    FULLSTACK = "fullstack"
    ML_DS = "ml_ds"
    FINTECH = "fintech"
    BLOCKCHAIN = "blockchain"
    DATA_ANALYSIS = "data_analysis"
    OTHER = "other"


def utcnow():
    return datetime.now(timezone.utc)


class Job(Base):
    """A job listing scraped from an external source."""
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), nullable=True, index=True)
    source = Column(String(50), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    company = Column(String(300), nullable=False)
    location = Column(String(300), default="Remote")
    description = Column(Text, default="")
    url = Column(String(1000), nullable=False)
    posted_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, default=utcnow)
    tags = Column(JSON, default=list)
    salary_range = Column(String(200), nullable=True)
    is_remote = Column(Boolean, default=True)
    category = Column(Enum(JobCategory), default=JobCategory.OTHER)
    fingerprint = Column(String(64), nullable=True, index=True, unique=True)

    # Relationships
    score = relationship("JobScore", back_populates="job", uselist=False, cascade="all, delete-orphan")
    application = relationship("Application", back_populates="job", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job id={self.id} title='{self.title}' company='{self.company}'>"


class JobScore(Base):
    """Match score for a job against the user's resume."""
    __tablename__ = "job_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    match_score = Column(Float, default=0.0)
    keyword_hits = Column(JSON, default=list)
    category_score = Column(Float, default=0.0)
    skill_score = Column(Float, default=0.0)
    experience_score = Column(Float, default=0.0)
    recency_score = Column(Float, default=0.0)
    scored_at = Column(DateTime, default=utcnow)

    # Relationships
    job = relationship("Job", back_populates="score")

    def __repr__(self):
        return f"<JobScore job_id={self.job_id} score={self.match_score}>"


class Application(Base):
    """Tracks user's application status for a job."""
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.INTERESTED)
    applied_date = Column(DateTime, nullable=True)
    notes = Column(Text, default="")
    cover_letter_text = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # Relationships
    job = relationship("Job", back_populates="application")

    def __repr__(self):
        return f"<Application job_id={self.job_id} status='{self.status}'>"


class ScrapeLog(Base):
    """Audit trail for each scrape run."""
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(50), nullable=False)
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    jobs_found = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    errors = Column(Text, default="")
    status = Column(String(20), default="running")
