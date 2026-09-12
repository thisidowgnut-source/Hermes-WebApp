import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.config import config
from backend.routers import system, swarm as swarm_router, audio as audio_router, social as social_router, dohnut as dohnut_router
from backend.websockets import terminal, browser, swarm as swarm_ws, audio as audio_ws, hitl as hitl_ws
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
    
    yield
    
    # Shutdown
    logger.info("Shutting down Hermes WebApp")
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

@app.get("/")
def read_root():
    return FileResponse(os.path.join(config.STATIC_DIR, "index.html"))

# Metrics endpoint for Prometheus scraping
@app.get("/metrics")
def get_metrics():
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(metrics.get_metrics()["metrics"])

# JSON metrics endpoint
@app.get("/api/metrics")
def get_metrics_json():
    return metrics.get_metrics()["raw"]

if __name__ == "__main__":
    uvicorn.run(app, host=config.HOST, port=config.PORT)