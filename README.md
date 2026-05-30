# DynActigraph

**Dynamic activity detection and hotspot mapping on transmission graphs.**

DynActigraph learns, from operating points and contingencies, where the grid shows strong dynamic activity (hotspots). This repository trains those models (`main.py`) and runs inference on new cases (`DynActigraph.py`). Details: [`docs/`](docs/).

---

## Environment setup

From the project root (`DynActigraph/`).

### Option A — venv

```bash
cd "/path/to/DynActigraph"
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### Option B — Conda

```bash
cd "/path/to/DynActigraph"
conda create -n dynactigraph python=3.10.15 -y
conda activate dynactigraph
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

**Dynawo** — install per [dynawo.github.io/install](https://dynawo.github.io/install/), then set `dynawo.path` in `config.yaml` to your environment script (`myEnvDynawo.sh` on Linux, or the Windows install folder / launcher from the Dynawo docs).

---

## Step 0 — Data folder and `config.yaml`

1. In `config.yaml`, set **`data.path`** to the folder where DynActigraph should keep all data (inputs and everything produced by `main.py`).

2. Create **`inputs/`** under that folder and add your cases:

```
<data.path>/
└── inputs/
    ├── contingencies.csv
    ├── operating_point_1/
    ├── operating_point_2/
    └── …
```

Each `operating_point_<N>/` folder must contain the Dynawo case (`*.iidm` or `*.xiidm`, `*.dyd`, `*.jobs`, `*.par`, and optionally `*.crt`).

3. Fill in **`config.yaml`** completely before running the pipeline (all sections below).

### `contingencies.csv`

Path: `<data.path>/inputs/contingencies.csv`

| Column | Description |
|--------|-------------|
| Contingency ID | e.g. `1l`, `2b`, `1g`, `1t`, `1lo` (type letter: `l` line, `b` bus, `g` generator, `t` transformer, `lo` load) |
| Fault name | Equipment id (see notes below per type) |
| Type | `line`, `bus`, `generator`, `transformer`, or `load` |
| Operating point | Optional; comma-separated OP indices (e.g. `38,39`), or empty for all OPs |

**Fault name by type**

| Type | Fault name | Dynawo event |
|------|------------|--------------|
| `line` | IIDM line id | `EventQuadripoleDisconnection` |
| `transformer` | IIDM two-winding transformer id | `EventQuadripoleDisconnection` (same as line) |
| `bus` | IIDM `bus` id (bus-breaker) or `busbarSection` id (node-breaker) | `EventConnectedStatus` |
| `load` | IIDM load id | `EventConnectedStatus` (same as bus) |
| `generator` | **Dynamic model id** from the case `.dyd`, not the IIDM static id | `EventSetPointBoolean` |

Example (for **bus**, use **Type** `bus` in both cases; **Fault name** is a `bus` id in bus-breaker models or a `busbarSection` id in node-breaker models):

| Contingency ID | Fault name | Type | Operating point |
|----------------|------------|------|-----------------|
| `1l` | `LINE_EXAMPLE_1` | `line` | |
| `1b` | `BUS_EXAMPLE_1` | `bus` | |
| `2b` | `BBS_EXAMPLE_1` | `bus` | |
| `1g` | `GEN_DM_EXAMPLE_1` | `generator` | |
| `1t` | `TRAFO_EXAMPLE_1` | `transformer` | |
| `1lo` | `LOAD_EXAMPLE_1` | `load` | "34, 38"|

`1b` / `BUS_EXAMPLE_1` — bus-breaker (`bus` id). `2b` / `BBS_EXAMPLE_1` — node-breaker (`busbarSection` id).

### `config.yaml`

| Section | Key | Options | Purpose |
|---------|-----|---------|---------|
| **dynactigraph** | `version` | string | Log header version |
| **dynawo** | `path` | path | Dynawo env script or install path |
| **data** | `path` | path | Data root (`inputs/` and all pipeline outputs) |
| **simulation** | `event_time` | float (s) | Fault time |
| | `initialization_duration` | float (s), or `0` / omit | Steady-state run before contingencies |
| **network** | `country_filter` | list, or `[]` | Country codes to keep; empty = no filter |
| **kpi** | `window_sec` | float (s) | KPI window length |
| | `step_sec` | float (s) | KPI window step |
| | `class_bins.voltage.cuts` | list of floats | Voltage class boundaries |
| | `class_bins.spower.cuts` | list of floats | Spower class boundaries |
| **model** | `num_classes` | integer ≥ 2 | Severity levels |
| **training** | `epochs` | integer | Max epochs per trial |
| | `patience` | integer | Early stopping |
| | `batch_size` | integer | Batch size |
| | `split_mode` | `scenario`, `operating_point` | How train/val/test split is built |
| | `seed` | integer | Random seed |
| | `training` | float | Train fraction or OP count |
| | `validation` | float | Validation fraction or OP count |
| | `testing` | float | Test fraction or OP count |
| | `high_class_threshold` | integer or `null` | Weighted sampling threshold; `null` = off |
| **optuna** | `n_trials` | integer | Hyperparameter trials |
| | `hparams.*` | see `config.yaml` | Optuna search spaces (`categorical`, `int`, `float`) |
| **inference** | `initialization_duration` | float (s), or `0` / omit | Steady-state run for `DynActigraph.py` |

---

## Step 1 — Run training (`main.py`)

```bash
python3 main.py
```

`main.py` writes under `<data.path>/` (graphs, KPIs, datasets, `Simulations_Scenarios/`, log, trained models). On success:

- `<data.path>/model/gat_voltage_best_model.pt`
- `<data.path>/model/gat_spower_best_model.pt`
- `<data.path>/dynactigraph.log`

---

## Inference (`DynActigraph.py`)

```bash
python3 DynActigraph.py --case-dir /path/to/operating_point --events-csv /path/to/events.csv
```

**`events.csv`** — one row per scenario:

| Column | Description |
|--------|-------------|
| `scenario_id` | Integer label (output subfolder name) |
| `Event` | Fault component id on the graph (same namespace as training contingencies) |

| scenario_id | Event |
|-------------|-------|
| `1` | `<fault_component_id_1>` |
| `2` | `<fault_component_id_2>` |

**Outputs** (under `<case-dir>/dynactigraph_output/`):

- `electrical_distance.csv`
- `scenario_<id>/prediction_voltage.csv`, `prediction_spower.csv`

---

## Nordic example — train on bundled data

The repository includes a ready-made **Nordic** case under `examples/Nordic/`: 10 operating points, `contingencies.csv` (lines, buses, generators, loads, transformers), and Dynawo inputs. Use it to run the full training pipeline end to end.

### What is in `examples/Nordic/`

```
examples/Nordic/
└── data/
    └── inputs/
        ├── contingencies.csv
        ├── operating_point_1/   … Nordic.xiidm, Nordic.dyd, Nordic.jobs, …
        ├── operating_point_2/
        …
        └── operating_point_10/
```

- **Lines / transformers / loads** — **Fault name** is the IIDM equipment id (e.g. `L1011-1013a`, `Tr1-1041`, `01_1`).
- **Buses** — Nordic is **bus-breaker**; **Fault name** is a `bus` id (e.g. `1011_131`), not a `busbarSection` id.
- **Generators** — **Fault name** is the **dynamic model id** from `Nordic.dyd` (e.g. `g01`, `g02`), not the IIDM static id.

### Step 1 — Environment

Follow [Environment setup](#environment-setup) (venv or Conda, `pip install -r requirements.txt`, Dynawo installed).

### Step 2 — Configure `config.yaml` (quick smoke test)

Copy the block below into the project-root [`config.yaml`](config.yaml). Replace the two placeholder paths with **absolute** paths on your machine, then save:

- **`dynawo.path`** — your Dynawo environment script (e.g. `/path/to/dynawo/dynawo.sh` or `myEnvDynawo.sh`).
- **`data.path`** — the **absolute** path of `examples/Nordic/data`.

This is a minimal end-to-end run: `optuna.n_trials: 1`, `training.epochs: 2`, and fixed hyperparameters. For a full study, increase `optuna.n_trials`, widen `optuna.hparams`, and raise `training.epochs`; see the [`config.yaml`](#configyaml) reference table for all keys.

```yaml
# Configuration for DynActigraph scripts.
#
# Quick smoke test defaults for the bundled Nordic example (examples/Nordic/data).
# Before running main.py, set dynawo.path and data.path to absolute paths on your machine.

dynactigraph:
  version: 1

dynawo:
  path: "/absolute/path/to/myEnvDynawo.sh"

data:
  path: "/absolute/path/to/DynActigraph/examples/Nordic/data"

simulation:
  event_time: 10.0
  initialization_duration: 10.0  # steady-state init per OP before contingencies; use 0 to skip

network:
  country_filter: []

kpi:
  window_sec: 5.0
  step_sec: 1.0
  class_bins:
    voltage:
      cuts: [0.33, 0.66]  # 3 severity bins on [0, 1] + 1 flag class => model.num_classes: 4
    spower:
      cuts: [0.33, 0.66]

model:
  num_classes: 4

training:
  epochs: 30          # keep low for a quick smoke test
  patience: 8
  batch_size: 16
  split_mode: operating_point
  seed: 42
  training: 0.8
  validation: 0.1
  testing: 0.1
  high_class_threshold: null

optuna:
  n_trials: 5
  hparams:
    hidden_dim:
      type: categorical
      choices: [64, 128, 256]
    num_layers:
      type: int
      low: 2
      high: 4
    hidden_channels:
      type: categorical
      choices: [16, 32, 64]
    num_heads:
      type: categorical
      choices: [1, 2, 4, 8]
    dropout:
      type: float
      low: 0.1
      high: 0.5
    num_gnn_layers:
      type: int
      low: 2
      high: 4
    lr:
      type: float
      low: 1.0e-4
      high: 5.0e-3
      log: true
    weight_decay:
      type: float
      low: 1.0e-6
      high: 1.0e-3
      log: true
    under_penalty_lambda:
      type: float
      low: 0.0
      high: 2.0
    coral_prediction_threshold:
      type: float
      low: 0.3
      high: 0.7

inference:
  initialization_duration: 10.0  # steady-state run before graph build; use 0 to skip
```

### Step 3 — Run from the project root

```bash
cd "/absolute/path/to/DynActigraph"
source .venv/bin/activate   # if using venv
python3 main.py
```

`main.py` runs, in order: Dynawo simulations → graph assets → curve/KPI post-processing → dataset build → GAT training.

This example has **many** contingencies × 10 operating points; the first full run can take a long time. Progress and errors are written to:

- `<data.path>/dynactigraph.log`
- `<data.path>/Simulations_Scenarios/simulation_results.csv` (resume: successful scenarios are skipped on re-run)

### Step 4 — Check trained models

On success you should have:

- `examples/Nordic/data/model/gat_voltage_best_model.pt`
- `examples/Nordic/data/model/gat_spower_best_model.pt`

Intermediate outputs (graphs, KPI tables, datasets) live alongside them under `examples/Nordic/data/` (`op_graphs/`, `KPI_*`, `Dataset_*.csv`, `Simulations_Scenarios/`, etc.).

### Step 5 (optional) — Inference on one operating point

After training, point inference at one OP folder and an events file (same id namespace as `contingencies.csv`):

```bash
python3 DynActigraph.py \
  --case-dir "/absolute/path/to/DynActigraph/examples/Nordic/data/inputs/operating_point_1" \
  --events-csv "/path/to/events.csv"
```

Predictions are written under `<case-dir>/dynactigraph_output/`.
