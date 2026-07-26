"""Phase 12 — centralized logging configuration for the training pipeline."""
from __future__ import annotations

import logging
import sys
import time
from contextlib import contextmanager
from pathlib import Path


def configure_logging(log_path: Path, name: str = "training_pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False

    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

    log_path.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_path, mode="w")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    return logger


@contextmanager
def log_stage(logger: logging.Logger, stage_name: str):
    """Context manager that times a pipeline stage and logs start/end/exceptions/memory."""
    import psutil  # local import: only needed when a stage is actually timed
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1e6
    logger.info("STAGE START: %s (memory: %.1f MB)", stage_name, mem_before)
    t0 = time.time()
    try:
        yield
    except Exception:
        logger.exception("STAGE FAILED: %s", stage_name)
        raise
    else:
        elapsed = time.time() - t0
        mem_after = process.memory_info().rss / 1e6
        logger.info(
            "STAGE END: %s (elapsed: %.2fs, memory: %.1f MB, delta: %+.1f MB)",
            stage_name, elapsed, mem_after, mem_after - mem_before,
        )
