import structlog
import logging
import os
from flask import request, has_request_context
from logging.handlers import RotatingFileHandler

LOG_DIR = os.environ.get('LOG_DIR', 'logs')


def add_request_info(_, __, event_dict):
    if has_request_context():
        event_dict["ip"] = request.remote_addr
        event_dict["user_agent"] = request.headers.get("User-Agent", "-")
        event_dict["path"] = request.path
        event_dict["method"] = request.method

    return event_dict


def setup_logging():
    os.makedirs(LOG_DIR, exist_ok=True)

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=5000000,
        backupCount=2
    )

    console_handler = logging.StreamHandler()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            add_request_info,
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set up root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Set up logging for Flask
    logging.getLogger("werkzeug").setLevel(logging.WARNING)


def get_logger(name):
    return structlog.get_logger(name)
