"""FastAPI application entry point with scheduler and CORS."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown lifecycle."""
    # Startup
    logger.info("🚀 Starting Remote Job Search Automation...")
    await init_db()
    logger.info("✅ Database initialized")

    # Start scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        scheduler = AsyncIOScheduler()

        async def scheduled_pipeline():
            """Run scrape + score + notify pipeline."""
            from app.database import async_session
            from app.services.aggregator import Aggregator
            from app.services.matcher import Matcher
            from app.services.notifier import Notifier

            async with async_session() as db:
                logger.info("⏰ Running scheduled scrape pipeline...")
                aggregator = Aggregator(db)
                await aggregator.run_full_scrape()

                matcher = Matcher(db)
                await matcher.score_all_jobs()

                notifier = Notifier(db)
                result = await notifier.send_daily_digest()
                logger.info(f"📬 Digest sent: {result}")

        # Run at configured hour daily
        scheduler.add_job(
            scheduled_pipeline,
            CronTrigger(hour=settings.NOTIFICATION_HOUR, minute=0),
            id="daily_pipeline",
            name="Daily Scrape + Score + Notify",
        )
        scheduler.start()
        logger.info(f"⏰ Scheduler started — daily pipeline at {settings.NOTIFICATION_HOUR}:00 UTC")
    except ImportError:
        logger.warning("APScheduler not installed — scheduled tasks disabled")

    yield

    # Shutdown
    try:
        scheduler.shutdown()
    except Exception:
        pass
    logger.info("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Remote Job Search Automation",
    description="Job aggregation, matching, and application assistance for freshers",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.routers import jobs, applications, cover_letters

app.include_router(jobs.router)
app.include_router(applications.router)
app.include_router(cover_letters.router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "remote-job-search"}


@app.post("/api/notify")
async def trigger_notification():
    """Manually trigger a notification digest."""
    from app.database import async_session
    from app.services.notifier import Notifier

    async with async_session() as db:
        notifier = Notifier(db)
        result = await notifier.send_daily_digest()
        return result


@app.post("/api/rescore")
async def rescore_all():
    """Re-score all jobs against the resume (use after updating resume.json)."""
    from app.database import async_session
    from app.services.matcher import Matcher

    async with async_session() as db:
        matcher = Matcher(db)
        count = await matcher.rescore_all()
        return {"rescored": count}
