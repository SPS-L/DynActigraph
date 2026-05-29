# `pipeline_logging.py`

Unified logging for **`main.py`** and all `src/` pipeline stages.

## Used by

- `main.py`, `src/simulate.py`, `src/build_op_assets.py`, `src/curves_post_process.py`, `src/dataset_construction.py`, `src/training.py`

## Outputs

| Path | Content |
|------|---------|
| `data/dynactigraph.log` | Single log file per `main.py` run (recreated each run) |

## Main API

| Function | Description |
|----------|-------------|
| `configure_pipeline_logging(log_path=None, ...)` | Set up file + console handlers and optional stdout tee |
| `get_logger()` | Return the `dynactigraph` logger (auto-configures if needed) |
| `get_pipeline_log_path()` | Resolved log file path |
| `log_step_banner(step_name)` | Write a `STEP: …` section header |

## Notes

- `DynActigraph.py` uses its own console logger and does **not** write to `data/dynactigraph.log`.
- Dynawo simulation messages from `simulate` are appended to `data/dynactigraph.log` via `dynawo_runner.append_simulation_log`.
