"""Email and Telegram notification service for daily job digests."""

import logging
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Job, JobScore

logger = logging.getLogger(__name__)


class Notifier:
    """Sends daily digest notifications via Email and/or Telegram."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def send_daily_digest(self) -> dict:
        """Send daily digest of top matching new jobs."""
        # Get jobs scraped in the last 24 hours with scores
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await self.db.execute(
            select(Job, JobScore)
            .join(JobScore, Job.id == JobScore.job_id)
            .where(Job.scraped_at >= cutoff)
            .order_by(desc(JobScore.match_score))
            .limit(10)
        )
        rows = result.all()

        if not rows:
            logger.info("No new jobs to notify about")
            return {"telegram": False, "email": False, "jobs_count": 0}

        jobs_data = []
        for job, score in rows:
            jobs_data.append({
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "score": score.match_score,
                "url": job.url,
                "source": job.source,
                "posted_date": job.posted_date,
            })

        telegram_sent = False
        email_sent = False

        # Send Telegram
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            telegram_sent = await self._send_telegram(jobs_data)

        # Send Email
        if settings.SMTP_USER and settings.NOTIFICATION_EMAIL:
            email_sent = await self._send_email(jobs_data)

        return {
            "telegram": telegram_sent,
            "email": email_sent,
            "jobs_count": len(jobs_data),
        }

    async def _send_telegram(self, jobs: list[dict]) -> bool:
        """Send digest via Telegram bot."""
        try:
            import httpx

            # Build message
            lines = ["🔍 <b>Daily Job Digest</b>\n"]
            for i, job in enumerate(jobs, 1):
                score_emoji = "🟢" if job["score"] >= 50 else "🟡" if job["score"] >= 30 else "🔴"
                lines.append(
                    f"{i}. {score_emoji} <b>{job['title']}</b>\n"
                    f"   🏢 {job['company']} | 📍 {job['location']}\n"
                    f"   📊 Match: {job['score']:.0f}/100 | 🔗 <a href=\"{job['url']}\">Apply</a>\n"
                )

            lines.append(f"\n📊 Total: {len(jobs)} new matches")
            message = "\n".join(lines)

            # Send via Telegram Bot API
            async with httpx.AsyncClient() as client:
                url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                resp = await client.post(url, json={
                    "chat_id": settings.TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                })
                resp.raise_for_status()

            logger.info("Telegram digest sent successfully")
            return True

        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return False

    async def _send_email(self, jobs: list[dict]) -> bool:
        """Send digest via email."""
        try:
            # Build HTML email
            html_body = self._build_email_html(jobs)

            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"🔍 Daily Job Digest — {len(jobs)} New Matches"
            msg["From"] = settings.SMTP_USER
            msg["To"] = settings.NOTIFICATION_EMAIL
            msg.attach(MIMEText(html_body, "html"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info("Email digest sent successfully")
            return True

        except Exception as e:
            logger.error(f"Email notification failed: {e}")
            return False

    def _build_email_html(self, jobs: list[dict]) -> str:
        """Build HTML email body."""
        rows = ""
        for job in jobs:
            score_color = "#10b981" if job["score"] >= 50 else "#f59e0b" if job["score"] >= 30 else "#ef4444"
            posted = job["posted_date"].strftime("%b %d") if job["posted_date"] else "N/A"
            rows += f"""
            <tr>
                <td style="padding:12px;border-bottom:1px solid #1e293b;">
                    <strong>{job['title']}</strong><br>
                    <span style="color:#94a3b8;">{job['company']} • {job['location']}</span>
                </td>
                <td style="padding:12px;border-bottom:1px solid #1e293b;text-align:center;">
                    <span style="background:{score_color};color:white;padding:4px 12px;border-radius:20px;font-weight:bold;">
                        {job['score']:.0f}
                    </span>
                </td>
                <td style="padding:12px;border-bottom:1px solid #1e293b;color:#94a3b8;">{posted}</td>
                <td style="padding:12px;border-bottom:1px solid #1e293b;">
                    <a href="{job['url']}" style="color:#3b82f6;text-decoration:none;">Apply →</a>
                </td>
            </tr>
            """

        return f"""
        <html>
        <body style="margin:0;padding:20px;background:#0f172a;color:#e2e8f0;font-family:Inter,system-ui,sans-serif;">
            <div style="max-width:700px;margin:0 auto;background:#1e293b;border-radius:16px;overflow:hidden;">
                <div style="padding:24px;background:linear-gradient(135deg,#1e3a5f,#0f172a);text-align:center;">
                    <h1 style="color:#3b82f6;margin:0;">🔍 Daily Job Digest</h1>
                    <p style="color:#94a3b8;margin:8px 0 0;">{len(jobs)} new matching jobs found</p>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#0f172a;">
                            <th style="padding:12px;text-align:left;color:#3b82f6;">Job</th>
                            <th style="padding:12px;text-align:center;color:#3b82f6;">Score</th>
                            <th style="padding:12px;text-align:left;color:#3b82f6;">Date</th>
                            <th style="padding:12px;text-align:left;color:#3b82f6;">Link</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                <div style="padding:16px;text-align:center;color:#64748b;font-size:13px;">
                    Remote Job Search Automation • Powered by Python + FastAPI
                </div>
            </div>
        </body>
        </html>
        """
