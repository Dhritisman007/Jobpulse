"""Cover letter generation API endpoints."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import CoverLetterRequest, CoverLetterResponse
from app.services.cover_letter import CoverLetterGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/cover-letters", tags=["cover-letters"])


@router.post("/generate", response_model=CoverLetterResponse)
async def generate_cover_letter(
    data: CoverLetterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a tailored cover letter for a specific job."""
    generator = CoverLetterGenerator(db)

    try:
        cover_letter = await generator.generate(data.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Cover letter generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate cover letter")

    return CoverLetterResponse(
        job_id=data.job_id,
        cover_letter=cover_letter,
        generated_at=datetime.now(timezone.utc),
    )
