import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import config
from backend.auth import telegram_auth_guard
from backend.routers import system, swarm as swarm_router, audio as audio_router, social as social_router, dohnut as dohnut_router, auth as auth_router, missions as missions_router, reach as reach_router
from backend.websockets import terminal, browser, swarm as swarm_ws, audio as audio_ws, hitl as hitl_ws, missions as missions_ws
from backend.bot_bridge import init_bot_bridge, stop_bot_polling
from backend.observability import setup_logging, metrics, init_telegram_alerter

logger = setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    json_logs=os.getenv("JSON_LOGS", "true").lower() == "true",
    log_file=os.getenv("LOG_FILE")
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Hermes WebApp", version="1.0.0")
    
    # Initialize Telegram alerter if configured
    if config.TELEGRAM_BOT_TOKEN:
        try:
            init_telegram_alerter(config.TELEGRAM_BOT_TOKEN, "@HermesOS_Channel")
            logger.info("Telegram alerter initialized")
        except Exception as e:
            logger.warning("Could not initialize Telegram alerter", error=str(e))
        
        try:
            logger.info("Initializing Telegram Bot Bridge (outbound-only, NO polling)...")
            await init_bot_bridge()
        except Exception as e:
            logger.warning("Could not initialize Bot Bridge", error=str(e))
    else:
        logger.info("TELEGRAM_BOT_TOKEN not set; skipping Bot Bridge initialization.")

    # Reconcile incomplete mission runs across restart
    try:
        from backend.services.mission_service import MissionService
        mission_service = MissionService()
        reconciliation = mission_service.reconcile_startup()
        if reconciliation.reconciled_count > 0:
            logger.info("Reconciled dangling mission runs", count=reconciliation.reconciled_count)
    except Exception as e:
        logger.warning("Startup mission reconciliation warning", error=str(e))

    # Initialize and start Durable Scheduler background worker
    scheduler_task = None
    try:
        from backend.services.durable_scheduler import get_durable_scheduler
        scheduler = get_durable_scheduler()
        scheduler.reconcile_startup()

        async def _scheduler_loop():
            logger.info("Durable Scheduler background poller started")
            while True:
                try:
                    await asyncio.sleep(5)
                    executed = await scheduler.poll_and_execute_due_jobs()
                    if executed > 0:
                        logger.info("Durable Scheduler executed due jobs", count=executed)
                except asyncio.CancelledError:
                    break
                except Exception as poll_err:
                    logger.warning("Durable Scheduler poller error", error=str(poll_err))

        scheduler_task = asyncio.create_task(_scheduler_loop())
    except Exception as e:
        logger.warning("Could not initialize Durable Scheduler worker", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hermes WebApp")
    if scheduler_task and not scheduler_task.done():
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass

    if config.TELEGRAM_BOT_TOKEN:
        try:
            logger.info("Closing Telegram Bot Bridge session...")
            await stop_bot_polling()
        except Exception as e:
            logger.error("Error closing Bot Bridge", error=str(e))

app = FastAPI(title="Hermes WebApp Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=config.ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=config.STATIC_DIR), name="static")

# Include Routers
app.include_router(auth_router.router)
app.include_router(system.router)
app.include_router(swarm_router.router)
app.include_router(audio_router.router)
app.include_router(social_router.router)
app.include_router(dohnut_router.router)
app.include_router(terminal.router)
app.include_router(browser.router)
app.include_router(swarm_ws.router)
app.include_router(audio_ws.router)
app.include_router(hitl_ws.router)
app.include_router(missions_router.router)
app.include_router(missions_ws.router)
app.include_router(reach_router.router)

@app.get("/")
def read_root():
    return FileResponse(os.path.join(config.STATIC_DIR, "index.html"))

# Metrics endpoint for Prometheus scraping
@app.get("/metrics")
def get_metrics(operator: dict = Depends(telegram_auth_guard)):
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(metrics.get_metrics()["metrics"])

# JSON metrics endpoint
@app.get("/api/metrics")
def get_metrics_json(operator: dict = Depends(telegram_auth_guard)):
    return metrics.get_metrics()["raw"]

if __name__ == "__main__":
    uvicorn.run(app, host=config.HOST, port=config.PORT)