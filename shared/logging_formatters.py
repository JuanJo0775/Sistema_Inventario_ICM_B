"""JSON log formatter for production (MEDIA-15)."""

from __future__ import annotations

import json
import logging
import traceback


class JsonFormatter(logging.Formatter):
    """Emits each log record as a single-line JSON object for structured log pipelines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "level": record.levelname,
            "time": self.formatTime(record, self.datefmt),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        if record.exc_info:
            payload["exc_info"] = traceback.format_exception(*record.exc_info)
        # Attach any extra fields passed via extra={} on the log call
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
            } and not key.startswith("_"):
                try:
                    json.dumps(value)
                    payload[key] = value
                except (TypeError, ValueError):
                    payload[key] = str(value)
        return json.dumps(payload, ensure_ascii=False, default=str)
