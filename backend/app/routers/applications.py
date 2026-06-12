"""Application tracking API endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models import Job, Application, ApplicationStatus
from app.schemas import ApplicationUpdate, ApplicationResponse, JobResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.put("/{job_id}")
async def update_application(
    job_id: int,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Create or update application status for a job."""
    # Verify job exists
    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Find existing application
    result = await db.execute(
        select(Application).where(Application.job_id == job_id)
    )
    app = result.scalar_one_or_none()

    try:
        status_enum = ApplicationStatus(data.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in ApplicationStatus]}"
        )

    if app:
        app.status = status_enum
        if data.notes is not None:
            app.notes = data.notes
        if data.applied_date:
            app.applied_date = data.applied_date
        elif status_enum == ApplicationStatus.APPLIED and not app.applied_date:
            app.applied_date = datetime.now(timezone.utc)
        app.updated_at = datetime.now(timezone.utc)
    else:
        app = Application(
            job_id=job_id,
            status=status_enum,
            notes=data.notes or "",
            applied_date=data.applied_date or (
                datetime.now(timezone.utc) if status_enum == ApplicationStatus.APPLIED else None
            ),
        )
        db.add(app)

    await db.commit()
    await db.refresh(app)

    return {
        "id": app.id,
        "job_id": app.job_id,
        "status": app.status.value,
        "applied_date": app.applied_date.isoformat() if app.applied_date else None,
        "notes": app.notes,
        "updated_at": app.updated_at.isoformat(),
    }


@router.get("")
async def list_applications(
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List all applications with optional status filter."""
    query = (
        select(Application)
        .options(joinedload(Application.job).joinedload(Job.score))
        .order_by(desc(Application.updated_at))
    )

    if status:
        query = query.where(Application.status == status)

    result = await db.execute(query)
    applications = result.unique().scalars().all()

    return [
        {
            "id": app.id,
            "job_id": app.job_id,
            "status": app.status.value,
            "applied_date": app.applied_date.isoformat() if app.applied_date else None,
            "notes": app.notes,
            "cover_letter_text": app.cover_letter_text,
            "created_at": app.created_at.isoformat(),
            "updated_at": app.updated_at.isoformat(),
            "job": {
                "id": app.job.id,
                "title": app.job.title,
                "company": app.job.company,
                "url": app.job.url,
                "source": app.job.source,
                "location": app.job.location,
                "match_score": app.job.score.match_score if app.job.score else None,
            } if app.job else None,
        }
        for app in applications
    ]


@router.delete("/{job_id}")
async def delete_application(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove application tracking for a job."""
    result = await db.execute(
        select(Application).where(Application.job_id == job_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    await db.delete(app)
    await db.commit()
    return {"status": "deleted"}
