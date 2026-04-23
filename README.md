# FANUC Trajectory Pipeline

This repository converts semicolon-separated trajectory CSV files into FANUC `.LS` programs, applies waypoint preprocessing, uploads the generated program over FTP, and records prepared runs in a JSONL manifest.

## What The Pipeline Does

1. Reads raw trajectory CSV files with columns `timestep;x;y;z;w;p;r`.
2. Computes Cartesian step velocity in `mm/s`.
3. Quantizes velocity into configurable bands and reduces the trajectory to segment boundaries.
4. Flips the Z axis and translates the trajectory so the first waypoint lands at a configured target origin.
5. Generates either a Cartesian `L` motion program or a joint `J` motion program in FANUC `.LS` format.
6. Uploads the `.LS` file to the selected controller target via FTP.
7. Appends a `prepared_trajectory` record to `src/config/run_manifest.jsonl`.

## Important Defaults

Review these values before running the batch script:

- `src/main.py` defaults to `RUNTIME_TARGET = "REAL"`.
- `src/main.py` defaults to `MOVEMENT_TYPE = "JOINT"`.
- `src/main.py` defaults to `REMOTE_DIR = "FR:"`.
- `src/pipeline.py` maps `SIMULATION` to `127.0.0.1` and `REAL` to `10.147.229.170`.
- `src/run_manifest.py` expects shared folders under `K:\Test Trajectories`.

Running `python src/main.py` will attempt an FTP upload as part of the normal pipeline. Make sure the selected target, IP address, remote directory, and shared-drive paths are correct before running it.

## Input Format

The preprocessing step expects a semicolon-separated CSV with this header:

```text
timestep;x;y;z;w;p;r
```

Field meanings:

- `timestep`: timestamp in milliseconds
- `x`, `y`, `z`: Cartesian position in millimeters
- `w`, `p`, `r`: orientation angles in degrees

Example rows from `input_data/path_short.csv`:

```text
timestep;x;y;z;w;p;r
0;0;-80;-12;-176;1;84
4;0;-79.999992;-12.6;-176;1;84
8;0;-80;-13.2;-176;1;84
```

## Repository Layout

- `src/main.py`: batch entry point that discovers CSV files, assigns trajectory IDs, runs the pipeline, and writes manifest records.
- `src/pipeline.py`: orchestration layer that preprocesses input data, generates `.LS`, and uploads it.
- `src/preprocess_trajectory.py`: velocity quantization, waypoint reduction, Z flip, translation, and CNT assignment.
- `src/ascii_convert_joint.py`: joint-motion FANUC `.LS` generator using `J` instructions.
- `src/ascii_convert_cart.py`: Cartesian-motion FANUC `.LS` generator using `L` instructions.
- `src/upload.py`: FTP upload helper.
- `src/run_manifest.py`: manifest and ID allocation helpers.
- `input_data/`: sample CSV trajectories for local reference.

## Setup

The code imports `numpy`, `pandas`, and `scipy`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## How To Run

### Batch preparation

The default entry point is:

```powershell
python src/main.py
```

That command will:

- scan `DEFAULT_MUJOCO_DIR` for `*.csv`
- generate `.LS` files in `DEFAULT_LS_OUTPUT_DIR`
- write quantized waypoint CSVs alongside the `.LS` files
- upload the `.LS` files to the configured FANUC target
- append records to `src/config/run_manifest.jsonl`

### Configuration points

Update these files when changing behavior:

- `src/main.py`: batch defaults such as runtime target, remote directory, and movement type
- `src/pipeline.py`: target origin, velocity quantization band, CNT value, and runtime target IP mapping
- `src/run_manifest.py`: default input, output, and results directories

## Outputs

For each processed trajectory, the pipeline generates:

- a FANUC `.LS` program such as `MJ0001.LS`
- a quantized waypoint CSV such as `MJ0001_quantized.csv`
- a manifest record describing the prepared artifact

The manifest currently supports two record types:

- `prepared_trajectory`: written by the batch preparation flow in `src/main.py`
- `captured_run`: supported by helper functions in `src/run_manifest.py`, but not wired to a top-level script in this repository yet

## Notes

- Sample files in `input_data/` are useful for understanding the CSV format, but `src/main.py` does not read from that folder unless you reconfigure the source directory.
- The joint-motion export still writes Cartesian `P[...]` position records; it only changes the FANUC motion instructions from `L` to `J`.
- The final waypoint always receives `FINE`; intermediate waypoints use the configured CNT value.
