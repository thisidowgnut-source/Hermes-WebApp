"""
Structured Logging & Observability for Hermes WebApp
=====================================================
Uses structlog for structured JSON logging with context.
Integrates with evlog-style wide events for analysis.
"""

import os
import sys
import json
import time
import logging
import structlog
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path
from contextvars import ContextVar

# Context variables for request correlation
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
agent_id_var: ContextVar[Optional[str]] = ContextVar("agent_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def setup_logging(
    level: str = "INFO",
    json_logs: bool = True,
    log_file: Optional[str] = None
) -> structlog.BoundLogger:
    """Configure structured logging for the application."""
    
    # Standard library logging setup
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        stream=sys.stdout,
    )
    
    # Configure structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
    ]
    
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(file=open(log_file, "a") if log_file else sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    return structlog.get_logger()


def get_logger(name: str = "hermes") -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


# Wide Event Schema (evlog-style)
class WideEvent:
    """Wide event for structured logging - single line with all context."""
    
    @staticmethod
    def create(
        event_type: str,
        message: str,
        level: str = "info",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a wide event dict with standard fields."""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event_type": event_type,
            "message": message,
            "service": "hermes-webapp",
            "version": "1.0.0",
            "request_id": request_id_var.get(),
            "agent_id": agent_id_var.get(),
            "user_id": user_id_var.get(),
            **kwargs
        }
    
    @staticmethod
    def log(logger: structlog.BoundLogger, event_type: str, message: str, level: str = "info", **kwargs):
        """Log a wide event."""
        event = WideEvent.create(event_type, message, level, **kwargs)
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(message, **event)


# Predefined event types for consistency
class EventTypes:
    # System events
    STARTUP = "system.startup"
    SHUTDOWN = "system.shutdown"
    HEALTH_CHECK = "system.health_check"
    
    # HTTP events
    HTTP_REQUEST = "http.request"
    HTTP_RESPONSE = "http.response"
    HTTP_ERROR = "http.error"
    
    # WebSocket events
    WS_CONNECT = "ws.connect"
    WS_DISCONNECT = "ws.disconnect"
    WS_MESSAGE = "ws.message"
    WS_ERROR = "ws.error"
    
    # Agent/Swarm events
    AGENT_SPAWN = "agent.spawn"
    AGENT_TERMINATE = "agent.terminate"
    AGENT_ERROR = "agent.error"
    AGENT_LOG = "agent.log"
    SWARM_TELEMETRY = "swarm.telemetry"
    
    # HITL events
    HITL_REQUEST = "hitl.request"
    HITL_RESPONSE = "hitl.response"
    HITL_TIMEOUT = "hitl.timeout"
    
    # Browser/Terminal events
    BROWSER_ACTION = "browser.action"
    TERMINAL_COMMAND = "terminal.command"
    
    # Security events
    THREAT_DETECTED = "security.threat_detected"
    FIM_ALERT = "security.fim_alert"
    AUTH_ATTEMPT = "security.auth_attempt"
    
    # Telegram events
    TELEGRAM_ALERT_SENT = "telegram.alert_sent"
    TELEGRAM_WEBHOOK = "telegram.webhook"


# Request logging middleware helper
def log_request(logger: structlog.BoundLogger, method: str, path: str, status_code: int, duration_ms: float, **extra):
    """Log HTTP request as wide event."""
    WideEvent.log(
        logger,
        EventTypes.HTTP_RESPONSE,
        f"{method} {path} -> {status_code}",
        "info" if status_code < 400 else "warning",
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=round(duration_ms, 2),
        **extra
    )


# Agent logging helpers
def log_agent_event(logger: structlog.BoundLogger, agent_id: str, event_type: str, message: str, **extra):
    """Log agent event with agent context."""
    with structlog.contextvars.bound_contextvars(agent_id=agent_id):
        WideEvent.log(logger, event_type, message, **extra)


def log_hitl_event(logger: structlog.BoundLogger, session_id: str, event_type: str, message: str, **extra):
    """Log HITL event with session context."""
    WideEvent.log(logger, event_type, message, session_id=session_id, **extra)


# Metrics collection
class MetricsCollector:
    """Simple in-memory metrics collector for Prometheus-style metrics."""
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
        self._start_time = time.time()
    
    def increment(self, name: str, value: int = 1, labels: Dict[str, str] = None):
        key = self._make_key(name, labels)
        self.counters[key] = self.counters.get(key, 0) + value
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def observe(self, name: str, value: float, labels: Dict[str, str] = None):
        key = self._make_key(name, labels)
        if key not in self.histograms:
            self.histograms[key] = []
        self.histograms[key].append(value)
        # Keep only last 1000 observations
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics in Prometheus text format."""
        lines = []
        
        # Counters
        for key, value in self.counters.items():
            lines.append(f"# TYPE {key} counter")
            lines.append(f"{key} {value}")
        
        # Gauges
        for key, value in self.gauges.items():
            lines.append(f"# TYPE {key} gauge")
            lines.append(f"{key} {value}")
        
        # Histograms (summary)
        for key, values in self.histograms.items():
            if values:
                lines.append(f"# TYPE {key} summary")
                lines.append(f'{key}_count {len(values)}')
                lines.append(f'{key}_sum {sum(values):.6f}')
                lines.append(f'{key}_min {min(values):.6f}')
                lines.append(f'{key}_max {max(values):.6f}')
                lines.append(f'{key}_avg {sum(values)/len(values):.6f}')
        
        # Uptime
        lines.append(f"# TYPE hermes_uptime_seconds gauge")
        lines.append(f"hermes_uptime_seconds {time.time() - self._start_time:.0f}")
        
        return {"metrics": "\n".join(lines), "raw": {
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": {k: len(v) for k, v in self.histograms.items()}
        }}


# Global metrics instance
metrics = MetricsCollector()


# Telegram Alerting
class TelegramAlerter:
    """Send structured alerts to Telegram."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = get_logger("telegram_alerter")
    
    async def send_alert(
        self,
        title: str,
        message: str,
        level: str = "INFO",
        event_type: str = "alert",
        **context
    ):
        """Send formatted alert to Telegram."""
        import urllib.request
        
        level_emoji = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }.get(level.upper(), "📢")
        
        # Build context string
        context_lines = []
        for k, v in context.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            context_lines.append(f"  <code>{k}</code>: <code>{v}</code>")
        
        context_str = "\n".join(context_lines) if context_lines else "  <i>No additional context</i>"
        
        text = (
            f"{level_emoji} <b>[HERMES {level.upper()}]</b>\n"
            f"<b>{title}</b>\n\n"
            f"{message}\n\n"
            f"<b>Context:</b>\n{context_str}\n\n"
            f"<i>Event: {event_type} | {datetime.utcnow().isoformat()}Z</i>"
        )
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }).encode("utf-8")
        
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode())
            
            if result.get("ok"):
                self.logger.info("telegram_alert_sent", title=title, level=level)
                return True
            else:
                self.logger.error("telegram_alert_failed", error=result)
                return False
                
        except Exception as e:
            self.logger.error("telegram_alert_exception", error=str(e))
            return False
    
    async def send_metrics_summary(self):
        """Send periodic metrics summary."""
        m = metrics.get_metrics()
        raw = m["raw"]
        
        summary = (
            f"📊 <b>HERMES METRICS SUMMARY</b>\n\n"
            f"Counters: {len(raw['counters'])}\n"
            f"Gauges: {len(raw['gauges'])}\n"
            f"Histograms: {len(raw['histograms'])}\n\n"
            f"Key metrics:\n"
        )
        
        # Add top counters
        for k, v in sorted(raw["counters"].items(), key=lambda x: -x[1])[:10]:
            summary += f"  <code>{k}</code>: {v}\n"
        
        await self.send_alert("Metrics Summary", summary, "INFO", "metrics_summary")


# Global alerter instance (initialized on startup)
alerter: Optional[TelegramAlerter] = None


def init_telegram_alerter(bot_token: str, chat_id: str) -> TelegramAlerter:
    """Initialize global Telegram alerter."""
    global alerter
    alerter = TelegramAlerter(bot_token, chat_id)
    return alerter


async def send_alert(title: str, message: str, level: str = "INFO", **context):
    """Convenience function to send alert if alerter is initialized."""
    if alerter:
        return await alerter.send_alert(title, message, level, **context)
    return False