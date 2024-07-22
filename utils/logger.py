"""
Logging configuration module for the AION License Count application.

This module sets up structured logging using structlog and provides utility
functions for logging throughout the application.
"""

import structlog
import logging
import os
from flask import request, has_request_context
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from create_app import app

# Get the log directory from the app configuration
LOG_DIR = app.config["LOG_DIR"]


def fetch_log_dir():
    """
       Retrieve the configured log directory.

       Returns:
           str: Path to the log directory.
       """
    return LOG_DIR


def add_request_info(_, __, event_dict):
    """
        Add request-specific information to log events.

        This function is used as a processor in structlog configuration to
        add HTTP request details to log events when a request context is available.

        Args:
            _: Ignored (structlog passes the logger here)
            __: Ignored (structlog passes the method name here)
            event_dict (dict): The event dictionary to be logged

        Returns:
            dict: The event dictionary with added request information
        """
    if has_request_context():
        event_dict["ip"] = request.remote_addr
        event_dict["user_agent"] = request.headers.get("User-Agent", "-")
        event_dict["path"] = request.path
        event_dict["method"] = request.method

    return event_dict


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            log_record['timestamp'] = self.formatTime(record)
        if log_record.get('level'):
            log_record['level'] = record.levelname
        else:
            log_record['level'] = record.levelname
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        elif record.exc_text:
            log_record['exception'] = record.exc_text

    def formatException(self, exc_info):
        formatted = super().formatException(exc_info)
        return formatted.replace("\n", "\\n").replace("\r", "\\r")


def setup_logging():
    """
       Configure and set up logging for the application.

       This function sets up both file and console logging, configures structlog,
       and sets the logging level for the application and Flask's werkzeug logger.
       """

    # Ensure the log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    json_formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')

    # Set up a rotating file handler
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=5000000,  # 5 MB
        backupCount=2
    )
    file_handler.setFormatter(json_formatter)

    console_handler = logging.StreamHandler()
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    console_handler.setFormatter(console_format)

    # Set up a console handler
    console_handler = logging.StreamHandler()

    # Configure structlog
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
    """
        Get a structured logger with the given name.

        Args:
            name (str): The name for the logger, typically __name__ of the calling module.

        Returns:
            structlog.BoundLogger: A structured logger instance.
        """
    logger = logging.getLogger(name)
    return structlog.wrap_logger(
        logger,
        processors=[
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=dict,
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
