# AGENTS.md

## Purpose

This repository turns MuJoCo-style trajectory CSV files into FANUC `.LS` motion programs, uploads them over FTP, and records generated artifacts in a manifest.

## Safety-Critical Defaults

- `src/main.py` currently defaults to `RUNTIME_TARGET = "REAL"`.
- `src/pipeline.py` always calls `ftp_upload()` inside `run_pipeline()`.
- `src/pipeline.py` maps `REAL` to `10.147.229.170` and `SIMULATION` to `127.0.0.1`.
- `src/run_manifest.py` points to shared-drive folders under `K:\Test Trajectories`.

Do not run `python src/main.py` or call `run_pipeline()` unless the user explicitly wants an upload attempt. Prefer read-only inspection or pure preprocessing steps when validating changes.

## Data Contract

The expected raw CSV format is semicolon-separated with these columns:

```text
timestep;x;y;z;w;p;r
```

Units:

- `timestep` in milliseconds
- `x`, `y`, `z` in millimeters
- `w`, `p`, `r` in degrees

Generated outputs include:

- `*.LS` FANUC programs
- `*_quantized.csv` waypoint exports
- `src/config/run_manifest.jsonl` runtime metadata

These generated artifacts should stay out of version control unless the user asks otherwise.

## File Map

- `src/main.py`: batch discovery, ID allocation, pipeline execution, manifest append
- `src/pipeline.py`: preprocess -> LS generation -> FTP upload
- `src/preprocess_trajectory.py`: waypoint reduction, velocity quantization, coordinate transform, CNT assignment
- `src/ascii_convert_joint.py`: joint-style LS generation
- `src/ascii_convert_cart.py`: Cartesian-style LS generation
- `src/upload.py`: FTP transfer helper
- `src/run_manifest.py`: manifest, run IDs, trajectory IDs, and output directory helpers

## Working Guidelines

- Keep the CSV column contract stable unless the user explicitly requests a format change.
- If you change runtime defaults, update both `README.MD` and this file in the same task.
- Avoid changing controller IPs, shared-drive roots, or upload targets without calling out the operational impact.
- Prefer local validation that does not touch FTP or external network paths.
- Preserve sample data under `input_data/`; it is documentation as much as test input.

## Validation Approach

Safe validation options:

- run pure functions such as `preprocess()` on local sample CSVs
- inspect generated text from the LS converters without uploading
- review manifest helper behavior with temporary local paths

Risky validation options that should require explicit user intent:

- running `python src/main.py`
- invoking `run_pipeline()` with live defaults
- anything that reaches `ftp_upload()` against hardware or simulator infrastructure
