"""Resume-based job matching and scoring engine."""

import json
import logging
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Job, JobScore
from app.schemas import ResumeData
from app.scrapers.base import CATEGORY_KEYWORDS

logger = logging.getLogger(__name__)


class Matcher:
    """Scores jobs against the user's resume."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._resume: Optional[ResumeData] = None

    def _load_resume(self) -> ResumeData:
        """Load resume from JSON file."""
        if self._resume is not None:
            return self._resume

        resume_path = settings.resume_file
        if not resume_path.exists():
            logger.warning(f"Resume file not found at {resume_path}, using empty resume")
            self._resume = ResumeData()
            return self._resume

        try:
            with open(resume_path, "r") as f:
                data = json.load(f)
            self._resume = ResumeData(**data)
            logger.info(f"Loaded resume: {self._resume.name}, {len(self._resume.skills)} skills")
        except Exception as e:
            logger.error(f"Error loading resume: {e}")
            self._resume = ResumeData()

        return self._resume

    async def score_all_jobs(self) -> int:
        """Score all unscored jobs. Returns count of newly scored jobs."""
        resume = self._load_resume()

        # Get all jobs that haven't been scored yet
        result = await self.db.execute(
            select(Job).outerjoin(JobScore).where(JobScore.id.is_(None))
        )
        unscored_jobs = result.scalars().all()

        scored_count = 0
        for job in unscored_jobs:
            score = self._compute_score(job, resume)
            self.db.add(score)
            scored_count += 1

        if scored_count > 0:
            await self.db.commit()

        logger.info(f"Scored {scored_count} new jobs")
        return scored_count

    async def rescore_all(self) -> int:
        """Re-score all jobs (e.g. after resume update)."""
        resume = self._load_resume()

        # Delete all existing scores
        result = await self.db.execute(select(Job))
        all_jobs = result.scalars().all()

        # Clear old scores
        await self.db.execute(
            update(JobScore).values(match_score=0)
        )

        scored_count = 0
        for job in all_jobs:
            # Check if score exists
            existing = await self.db.execute(
                select(JobScore).where(JobScore.job_id == job.id)
            )
            existing_score = existing.scalar_one_or_none()

            score_data = self._compute_score(job, resume)

            if existing_score:
                existing_score.match_score = score_data.match_score
                existing_score.keyword_hits = score_data.keyword_hits
                existing_score.category_score = score_data.category_score
                existing_score.skill_score = score_data.skill_score
                existing_score.experience_score = score_data.experience_score
                existing_score.recency_score = score_data.recency_score
                existing_score.scored_at = datetime.now(timezone.utc)
            else:
                self.db.add(score_data)

            scored_count += 1

        await self.db.commit()
        logger.info(f"Re-scored {scored_count} jobs")
        return scored_count

    def _compute_score(self, job: Job, resume: ResumeData) -> JobScore:
        """Compute match score for a single job against the resume."""
        text = f"{job.title} {job.description} {' '.join(job.tags or [])}".lower()

        # 1. Skill overlap (40 pts)
        skill_hits = []
        all_resume_skills = [s.lower() for s in (resume.skills + resume.frameworks + resume.tools + resume.languages)]
        for skill in all_resume_skills:
            # Use word boundary matching for short skills
            if len(skill) <= 3:
                pattern = rf'\b{re.escape(skill)}\b'
                if re.search(pattern, text):
                    skill_hits.append(skill)
            elif skill in text:
                skill_hits.append(skill)

        unique_hits = list(set(skill_hits))
        skill_score = min(40, (len(unique_hits) / max(len(all_resume_skills), 1)) * 40)

        # 2. Framework/tool exact match (25 pts)
        # Bonus for high-value framework matches
        priority_tools = [
            "react", "fastapi", "python", "javascript", "typescript",
            "pytorch", "tensorflow", "docker", "kubernetes", "aws",
            "node.js", "nextjs", "next.js", "postgresql", "mongodb",
            "solidity", "rust", "go", "pandas", "scikit-learn",
        ]
        tool_matches = sum(1 for t in priority_tools if t in text)
        resume_tool_matches = sum(1 for t in priority_tools if t in ' '.join(all_resume_skills))
        overlap = sum(1 for t in priority_tools if t in text and t in ' '.join(all_resume_skills))
        framework_score = min(25, (overlap / max(1, min(tool_matches, resume_tool_matches))) * 25)

        # 3. Role category alignment (20 pts)
        category_score = 0.0
        job_cat = getattr(job, 'category', 'other')
        if job_cat and job_cat != 'other':
            # Check if job category matches target roles
            target_cats = self._get_target_categories(resume)
            if job_cat in target_cats:
                category_score = 20.0
            else:
                category_score = 5.0  # Some relevance for any tech role

        # 4. Experience level fit (10 pts)
        experience_score = 0.0
        fresher_terms = ["intern", "entry-level", "junior", "fresher", "new grad", "trainee", "graduate"]
        if any(term in text for term in fresher_terms):
            experience_score = 10.0
        elif not re.search(r'(\d+)\+?\s*(?:years?|yrs?)', text):
            experience_score = 7.0  # No experience mentioned = likely open
        else:
            # Check the minimum experience
            matches = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', text)
            if matches:
                min_exp = min(int(m) for m in matches)
                if min_exp <= 1:
                    experience_score = 8.0
                elif min_exp <= 2:
                    experience_score = 5.0

        # 5. Recency bonus (5 pts)
        recency_score = 0.0
        if job.posted_date:
            try:
                posted = job.posted_date
                if posted.tzinfo is None:
                    posted = posted.replace(tzinfo=timezone.utc)
                days_old = (datetime.now(timezone.utc) - posted).days
                if days_old <= 1:
                    recency_score = 5.0
                elif days_old <= 3:
                    recency_score = 4.0
                elif days_old <= 7:
                    recency_score = 2.0
            except Exception:
                pass

        total_score = round(skill_score + framework_score + category_score + experience_score + recency_score, 1)

        return JobScore(
            job_id=job.id,
            match_score=min(100, total_score),
            keyword_hits=unique_hits,
            category_score=category_score,
            skill_score=skill_score,
            experience_score=experience_score,
            recency_score=recency_score,
            scored_at=datetime.now(timezone.utc),
        )

    def _get_target_categories(self, resume: ResumeData) -> set:
        """Map resume target roles to job categories."""
        cats = set()
        for role in resume.target_roles:
            role_lower = role.lower()
            if any(kw in role_lower for kw in ["full-stack", "fullstack", "full stack", "web"]):
                cats.add("fullstack")
            if any(kw in role_lower for kw in ["machine learning", "ml", "data scien", "ai"]):
                cats.add("ml_ds")
            if any(kw in role_lower for kw in ["fintech", "quant", "financial"]):
                cats.add("fintech")
            if any(kw in role_lower for kw in ["blockchain", "web3", "crypto"]):
                cats.add("blockchain")
            if any(kw in role_lower for kw in ["data analy", "business analy", "analytics"]):
                cats.add("data_analysis")
        return cats if cats else {"fullstack", "ml_ds", "fintech", "blockchain", "data_analysis"}
