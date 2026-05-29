# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Sustainable Power Systems Laboratory (https://sps-lab.org/)
# Part of DynActigraph: Unified pipeline logging

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional, TextIO

from .paths import DATA_DIR

LOG_NAME = "dynactigraph"
DEFAULT_LOG_PATH = DATA_DIR / "dynactigraph.log"

_configured = False
_log_path: Path = DEFAULT_LOG_PATH


class _TeeStdout(TextIO):
    """Mirror stdout to the console and the pipeline log file."""

    def __init__(self, console: TextIO, log_handle: TextIO) -> None:
        self._console = console
        self._log_handle = log_handle

    def write(self, data: str) -> int:
        if not data:
            return 0
        self._console.write(data)
        self._console.flush()
        self._log_handle.write(data)
        self._log_handle.flush()
        return len(data)

    def flush(self) -> None:
        self._console.flush()
        self._log_handle.flush()

    def fileno(self) -> int:
        return self._console.fileno()

    def isatty(self) -> bool:
        return self._console.isatty()


def get_pipeline_log_path() -> Path:
    return _log_path


def configure_pipeline_logging(
    log_path: Optional[Path] = None,
    *,
    tee_stdout: bool = True,
    force: bool = False,
) -> logging.Logger:
    """Configure a single pipeline logger (file + console) and optional stdout tee."""
    global _configured, _log_path

    _log_path = (log_path or DEFAULT_LOG_PATH).resolve()
    _log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOG_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if _configured and not force:
        return logger

    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(_log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler(sys.__stdout__)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    if tee_stdout and not getattr(sys.stdout, "_dynactigraph_tee", False):
        log_handle = _log_path.open("a", encoding="utf-8")
        tee = _TeeStdout(sys.__stdout__, log_handle)
        tee._dynactigraph_tee = True  # type: ignore[attr-defined]
        sys.stdout = tee  # type: ignore[assignment]

    _configured = True
    return logger


def get_logger() -> logging.Logger:
    if not _configured:
        configure_pipeline_logging()
    return logging.getLogger(LOG_NAME)


def log_step_banner(step_name: str) -> None:
    """Write a visible section header for one pipeline step."""
    logger = get_logger()
    separator = "=" * 60
    logger.info(separator)
    logger.info("STEP: %s", step_name)
    logger.info(separator)
