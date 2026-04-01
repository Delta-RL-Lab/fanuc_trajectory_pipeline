# FANUC Trajectory Pipeline

Small Python pipeline for converting Cartesian trajectory CSV files into FANUC `.LS` programs and uploading them to a robot controller over FTP.

## What it does

The pipeline:

1. Loads a semicolon-separated trajectory CSV.
2. Computes Cartesian velocities from the timestep and XYZ positions.
3. Quantizes velocity into fixed bands.
4. Reduces the trajectory to waypoint segment boundaries.
5. Flips and translates coordinates to a target origin.
6. Generates a FANUC `.LS` program.
7. Uploads the generated file to the controller via FTP.

## Requirements

- Python 3.10+
- Network access to the FANUC controller if you want to upload files

Install dependencies:

```bash
pip install -r requirements.txt
```

## Input format

Input CSV files must be semicolon-separated and include these columns:

```text
timestep;x;y;z;w;p;r
```

- `timestep` is in milliseconds
- `x`, `y`, `z` are in millimeters
- `w`, `p`, `r` are in degrees

Sample inputs are included in [`input_data/path_short.csv`](/C:/Users/caldas/Documents/Projects/fanuc_trajectory_pipeline/input_data/path_short.csv), [`input_data/path_medium.csv`](/C:/Users/caldas/Documents/Projects/fanuc_trajectory_pipeline/input_data/path_medium.csv), and [`input_data/path_long.csv`](/C:/Users/caldas/Documents/Projects/fanuc_trajectory_pipeline/input_data/path_long.csv).

## Usage

Run from the repository root with Python on the `src` directory in `PYTHONPATH`:

```bash
$env:PYTHONPATH="src"
python -c "from pipeline import run_pipeline; run_pipeline('127.0.0.1', 'FR:', 'input_data/path_short.csv', 'TRAJSHORT.LS', 'TRAJSHORT')"
```

Replace:

- `'127.0.0.1'` with your FANUC controller IP
- `'FR:'` with the target controller directory if needed
- `'input_data/path_short.csv'` with your source CSV
- `'TRAJSHORT.LS'` and `'TRAJSHORT'` with your desired output filename and program name

## Using `main.py`

[`src/main.py`](/C:/Users/caldas/Documents/Projects/fanuc_trajectory_pipeline/src/main.py) is set up to run three jobs in sequence, but its CSV paths currently point to `../RL-Trajectory/...`. Update those paths to match files in this repository before using it.

Example:

```python
CSV_FILE = 'input_data/path_short.csv'
```

Then run:

```bash
python src/main.py
```

## Output

The pipeline generates a FANUC ASCII program file such as `TRAJSHORT.LS` in the working directory and then attempts to upload it with FTP.

## Project structure

```text
src/
  main.py
  pipeline.py
  preprocess_trajectory.py
  ascii_convert_cart.py
  upload.py
input_data/
  path_short.csv
  path_medium.csv
  path_long.csv
```
