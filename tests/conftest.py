"""Restore process-global resources changed by app and logging tests."""

import logging
from collections.abc import Iterator

import pytest


@pytest.fixture(autouse=True)
def restore_event_logger() -> Iterator[None]:
    logger = logging.getLogger("simply_simplify_language.events")
    handlers = logger.handlers[:]
    state = (logger.disabled, logger.level, logger.propagate)
    for handler in handlers:
        logger.removeHandler(handler)
    try:
        yield
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
        logger.disabled, logger.level, logger.propagate = state
        for handler in handlers:
            logger.addHandler(handler)
