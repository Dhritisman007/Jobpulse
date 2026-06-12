"""Claude API-powered cover letter generator."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Job, Application, ApplicationStatus
from app.schemas import ResumeData

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    """Generates tailored cover letters using Claude API."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate(self, job_id: int) -> str:
        """Generate a cover letter for a specific job."""
        # Fetch job
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Load resume
        resume = self._load_resume()

        # Build prompt
        prompt = self._build_prompt(job, resume)

        # Call Claude API
        cover_letter = await self._call_claude(prompt)

        # Save to application record
        await self._save_cover_letter(job_id, cover_letter)

        return cover_letter

    def _load_resume(self) -> ResumeData:
        """Load resume from JSON file."""
        resume_path = settings.resume_file
        if not resume_path.exists():
            return ResumeData()
        try:
            with open(resume_path, "r") as f:
                data = json.load(f)
            return ResumeData(**data)
        except Exception as e:
            logger.error(f"Error loading resume: {e}")
            return ResumeData()

    def _build_prompt(self, job: Job, resume: ResumeData) -> str:
        """Build the Claude API prompt for cover letter generation."""
        skills_str = ", ".join(resume.skills + resume.frameworks + resume.tools)
        projects_str = ""
        for p in resume.projects[:3]:
            projects_str += f"\n  - {p.get('name', 'Project')}: {p.get('description', '')}"

        return f"""Write a concise, personalized cover letter for a job application.

APPLICANT PROFILE:
- Name: {resume.name}
- Education: {json.dumps(resume.education) if resume.education else '3rd year CS undergraduate, AI/ML specialization'}
- Key Skills: {skills_str}
- Summary: {resume.summary}
- Notable Projects: {projects_str or 'Various AI/ML and full-stack projects'}

JOB DETAILS:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
- Description: {job.description[:2000]}

REQUIREMENTS:
1. Keep it under 300 words
2. Be professional but show genuine enthusiasm
3. Highlight 2-3 most relevant skills/projects that match the job
4. Show awareness of the company and role
5. End with a clear call to action
6. Do NOT include any placeholder text like [Your Name] — use the actual name
7. Format as plain text (no markdown)
8. If the applicant is a student/fresher, frame it as eagerness to learn and contribute

Write the cover letter now:"""

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API to generate the cover letter."""
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return self._generate_fallback(prompt)

        try:
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=api_key)
            message = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return message.content[0].text
        except ImportError:
            logger.warning("anthropic package not installed, using fallback")
            return self._generate_fallback(prompt)
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._generate_fallback(prompt)

    def _generate_fallback(self, prompt: str) -> str:
        """Generate a basic cover letter template when Claude is unavailable."""
        return (
            "⚠️ Claude API is not configured. Please set ANTHROPIC_API_KEY in your .env file.\n\n"
            "In the meantime, here's a template you can customize:\n\n"
            "Dear Hiring Manager,\n\n"
            "I am writing to express my strong interest in the [Position] role at [Company]. "
            "As a 3rd-year Computer Science student specializing in AI/ML, I bring a solid "
            "foundation in [relevant skills] and hands-on project experience.\n\n"
            "[Describe 2-3 relevant projects/skills here]\n\n"
            "I am eager to contribute to your team and grow as a developer. "
            "I would welcome the opportunity to discuss how my skills align with your needs.\n\n"
            "Best regards,\n"
            "[Your Name]"
        )

    async def _save_cover_letter(self, job_id: int, cover_letter: str):
        """Save cover letter to the application record."""
        result = await self.db.execute(
            select(Application).where(Application.job_id == job_id)
        )
        app = result.scalar_one_or_none()

        if app:
            app.cover_letter_text = cover_letter
            app.updated_at = datetime.now(timezone.utc)
        else:
            app = Application(
                job_id=job_id,
                status=ApplicationStatus.INTERESTED,
                cover_letter_text=cover_letter,
            )
            self.db.add(app)

        await self.db.commit()
