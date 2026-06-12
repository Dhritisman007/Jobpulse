"""Job listing API endpoints."""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, asc, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Job, JobScore, Application, ApplicationStatus
from app.schemas import (
    JobResponse, JobListResponse, JobCreate, ManualJobImport, ScrapeResult
)
from app.services.aggregator import Aggregator
from app.services.matcher import Matcher

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _job_to_response(job: Job) -> JobResponse:
    """Convert a Job ORM model to a response schema."""
    return JobResponse(
        id=job.id,
        external_id=job.external_id,
        source=job.source,
        title=job.title,
        company=job.company,
        location=job.location,
        description=job.description,
        url=job.url,
        posted_date=job.posted_date,
        scraped_at=job.scraped_at,
        tags=job.tags or [],
        salary_range=job.salary_range,
        is_remote=job.is_remote,
        category=job.category.value if job.category else "other",
        match_score=job.score.match_score if job.score else None,
        keyword_hits=job.score.keyword_hits if job.score else [],
        application_status=job.application.status.value if job.application else None,
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    category: str = Query(None, description="Filter by category"),
    source: str = Query(None, description="Filter by source"),
    status: str = Query(None, description="Filter by application status"),
    min_score: float = Query(None, description="Minimum match score"),
    search: str = Query(None, description="Search in title/company"),
    days_ago: int = Query(30, description="Jobs posted within N days"),
    sort_by: str = Query("match_score", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order"),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List jobs with filtering, sorting, and pagination."""
    # Base query
    query = (
        select(Job)
        .outerjoin(JobScore, Job.id == JobScore.job_id)
        .outerjoin(Application, Job.id == Application.job_id)
        .options(joinedload(Job.score), joinedload(Job.application))
    )

    # Filters
    if category:
        query = query.where(Job.category == category)
    if source:
        query = query.where(Job.source == source)
    if status:
        if status == "none":
            query = query.where(Application.id.is_(None))
        else:
            query = query.where(Application.status == status)
    if min_score is not None:
        query = query.where(JobScore.match_score >= min_score)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Job.title.ilike(search_term),
                Job.company.ilike(search_term),
                Job.description.ilike(search_term),
            )
        )
    if days_ago:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days_ago)
        query = query.where(
            or_(
                Job.posted_date >= cutoff,
                Job.posted_date.is_(None),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Sorting
    sort_col = {
        "match_score": JobScore.match_score,
        "posted_date": Job.posted_date,
        "company": Job.company,
        "title": Job.title,
        "scraped_at": Job.scraped_at,
    }.get(sort_by, JobScore.match_score)

    if sort_order == "desc":
        query = query.order_by(desc(sort_col).nullslast())
    else:
        query = query.order_by(asc(sort_col).nullsfirst())

    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    jobs = result.unique().scalars().all()

    return JobListResponse(
        jobs=[_job_to_response(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("/refresh", response_model=ScrapeResult)
async def refresh_jobs(
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full scrape from all sources, deduplicate, and score."""
    aggregator = Aggregator(db)
    result = await aggregator.run_full_scrape()

    # Score new jobs
    matcher = Matcher(db)
    scored = await matcher.score_all_jobs()

    result["scored"] = scored
    return result


@router.post("/import")
async def import_job(
    data: ManualJobImport,
    db: AsyncSession = Depends(get_db),
):
    """Manually import a job (e.g., from LinkedIn, Wellfound)."""
    from app.scrapers.base import RawJob
    from app.services.deduplicator import Deduplicator

    raw_job = RawJob(
        external_id=data.url,
        source=data.source,
        title=data.title or "Imported Job",
        company=data.company or "Unknown Company",
        description=data.description or "",
        url=data.url,
        is_remote=True,
    )
    raw_job.category = raw_job.detect_category()

    dedup = Deduplicator(db)
    is_new = await dedup.process_job(raw_job)
    await db.commit()

    if not is_new:
        return {"status": "duplicate", "message": "This job already exists in the database"}

    # Score the new job
    matcher = Matcher(db)
    await matcher.score_all_jobs()

    return {"status": "imported", "message": "Job imported and scored successfully"}


@router.get("/sources")
async def list_sources(db: AsyncSession = Depends(get_db)):
    """Get list of available sources and their job counts."""
    result = await db.execute(
        select(Job.source, func.count(Job.id))
        .group_by(Job.source)
    )
    return [{"source": row[0], "count": row[1]} for row in result.all()]


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics."""
    total_jobs = await db.execute(select(func.count(Job.id)))
    total_applied = await db.execute(
        select(func.count(Application.id))
        .where(Application.status == ApplicationStatus.APPLIED)
    )
    total_interested = await db.execute(
        select(func.count(Application.id))
        .where(Application.status == ApplicationStatus.INTERESTED)
    )
    avg_score = await db.execute(select(func.avg(JobScore.match_score)))

    return {
        "total_jobs": total_jobs.scalar() or 0,
        "total_applied": total_applied.scalar() or 0,
        "total_interested": total_interested.scalar() or 0,
        "avg_match_score": round(avg_score.scalar() or 0, 1),
    }


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single job by ID."""
    result = await db.execute(
        select(Job)
        .options(joinedload(Job.score), joinedload(Job.application))
        .where(Job.id == job_id)
    )
    job = result.unique().scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)
