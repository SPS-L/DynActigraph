# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Sustainable Power Systems Laboratory (https://sps-lab.org/)
# Part of DynActigraph: KPI, actions, and disconnections post-processing

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from modules.actions_detection import run_actions_detection
from modules.disconnections_detection import run_disconnections_detection
from modules.kpi import run_kpi
from modules.pipeline_logging import get_logger, log_step_banner


def main() -> None:
    log_step_banner("curves_post_process")
    logger = get_logger()

    logger.info("Step 1/3: KPI extraction")
    run_kpi()

    logger.info("Step 2/3: Actions detection")
    run_actions_detection()

    logger.info("Step 3/3: Disconnections detection")
    run_disconnections_detection()

    logger.info("curves_post_process completed.")
