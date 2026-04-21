"""Structured loguru configuration used by Jarvis services."""

from __future__ import annotations

import sys
from typing import Any

from loguru import logger


def configure_logging() -> None:
    """Configure the shared application logger."""

    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        backtrace=False,
        diagnose=False,
        serialize=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "{extra[component]} | {message}"
        ),
    )


def get_logger(component: str) -> Any:
    """Return a logger bound to a component name."""

    return logger.bind(component=component)
