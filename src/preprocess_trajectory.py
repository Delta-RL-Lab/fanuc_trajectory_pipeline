"""
preprocess_trajectory.py
------------------------
Converts a raw trajectory CSV into a preprocessed waypoint dataframe
ready for LS file generation.

Pipeline:
  1. Load raw CSV  (semicolon-separated: timestep;x;y;z;w;p;r)
  2. Compute per-step Cartesian velocity (mm/s) from timestep + XYZ
  3. Quantize velocity to nearest VELOCITY_QUANT mm/s band
  4. Reduce to segment-boundary waypoints (one row per velocity change)
  5. Flip Z axis  ->  z = -z
  6. Translate so that the first point lands at TARGET_ORIGIN
  7. Assign CNT values  (caller-selected blend term for intermediate, FINE for last)
  8. Return a clean DataFrame (and optionally save a CSV)

CLI usage:
  python preprocess_trajectory.py <input_csv> [output_csv]
"""

import sys
import numpy as np
import pandas as pd


# -- Defaults (override by passing arguments to preprocess()) -----------------

DEFAULT_TARGET_ORIGIN  = (-10.0, -10.0, -900.0)   # mm
DEFAULT_VELOCITY_QUANT = 5                          # mm/s quantisation step
DEFAULT_MIN_VELOCITY   = 1                          # mm/s floor
DEFAULT_CNT_VALUE      = "CNT100"


def normalize_cnt_value(cnt_value):
    """
    Normalize a caller-provided intermediate termination value.

    Accepted forms:
      - int 0..100           -> CNT<n>
      - "0".."100"           -> CNT<n>
      - "CNT0".."CNT100"     -> CNT<n>
      - "FINE"               -> FINE
    """

    if isinstance(cnt_value, int):
        if 0 <= cnt_value <= 100:
            return f"CNT{cnt_value}"
        raise ValueError("cnt_value integer must be between 0 and 100")

    if not isinstance(cnt_value, str):
        raise ValueError("cnt_value must be an int or string like 'CNT80' or 'FINE'")

    normalized = cnt_value.strip().upper()
    if normalized == "FINE":
        return normalized

    if normalized.isdigit():
        numeric_value = int(normalized)
        if 0 <= numeric_value <= 100:
            return f"CNT{numeric_value}"
        raise ValueError("cnt_value numeric string must be between 0 and 100")

    if normalized.startswith("CNT") and normalized[3:].isdigit():
        numeric_value = int(normalized[3:])
        if 0 <= numeric_value <= 100:
            return f"CNT{numeric_value}"

    raise ValueError("cnt_value must be 'FINE', an integer 0..100, or 'CNT0'..'CNT100'")


# -- Core function -------------------------------------------------------------

def preprocess(
    input_path,
    output_path=None,
    target_origin=DEFAULT_TARGET_ORIGIN,
    velocity_quant=DEFAULT_VELOCITY_QUANT,
    min_velocity=DEFAULT_MIN_VELOCITY,
    cnt_value=DEFAULT_CNT_VALUE,
):
    """
    Run the full preprocessing pipeline.

    Parameters
    ----------
    input_path : str
        Path to the raw semicolon-separated CSV
        (columns: timestep;x;y;z;w;p;r  --  timestep in ms, positions in mm).
    output_path : str or None
        If given, the result DataFrame is also written to this path as CSV.
    target_origin : tuple of float
        (x, y, z) in mm where the first waypoint should land after transform.
    velocity_quant : int or float
        Velocity quantisation step in mm/s.
    min_velocity : int or float
        Minimum allowed velocity in mm/s.
    cnt_value : int or str
        Intermediate FANUC termination value. The final waypoint is always FINE.

    Returns
    -------
    pd.DataFrame with columns:
        point_index, timestep_ms, x, y, z, w, p, r, velocity_mms, cnt
    """
    intermediate_cnt = normalize_cnt_value(cnt_value)

    # 1. Load
    df = pd.read_csv(input_path, sep=';')
    required = {'timestep', 'x', 'y', 'z', 'w', 'p', 'r'}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input CSV is missing columns: {missing}")
    print(f"  Loaded {len(df)} rows from '{input_path}'")

    # 2. Compute velocity (mm/s)
    dt_s = df['timestep'].diff() / 1000.0
    dist = np.sqrt(df['x'].diff()**2 + df['y'].diff()**2 + df['z'].diff()**2)
    raw_vel = dist / dt_s

    # Diagnose bad values. Row 0 always produces NaN from .diff() -- expected.
    # Only warn about additional bad values beyond row 0.
    bad_mask     = raw_vel.isna() | np.isinf(raw_vel)
    n_zero       = (dt_s.fillna(1) == 0).sum()
    n_unexpected = int(bad_mask.sum()) - (1 if bad_mask.iloc[0] else 0)
    if n_unexpected > 0 or n_zero > 0:
        print(f"  WARNING: {n_unexpected} unexpected bad velocity value(s) "
              f"({n_zero} duplicate/zero timestep(s)). Affected rows will be dropped.")
        bad_rows = df[bad_mask & (df.index > 0)][['timestep', 'x', 'y', 'z']].head(10)
        print(f"  Affected rows:\n{bad_rows.to_string(index=True)}")

    # Drop rows where timestep is duplicated (dt=0 → inf velocity)
    df = df[dt_s.fillna(1) > 0].copy()
    dt_s = df['timestep'].diff() / 1000.0
    dist = np.sqrt(df['x'].diff()**2 + df['y'].diff()**2 + df['z'].diff()**2)
    raw_vel = dist / dt_s

    # Forward-fill then backward-fill to cover any remaining NaNs
    # (only the first row should still be NaN after dropping zero-dt rows)
    df['velocity_mms'] = raw_vel.ffill().bfill()

    # Final guard: replace any surviving inf/NaN with min_velocity
    still_bad = df['velocity_mms'].isna() | np.isinf(df['velocity_mms'])
    if still_bad.any():
        print(f"  WARNING: {still_bad.sum()} velocity values could not be recovered; "
              f"clamping to min_velocity={min_velocity} mm/s.")
        df.loc[still_bad, 'velocity_mms'] = float(min_velocity)

    # 3. Quantise velocity
    df['vel_q'] = (df['velocity_mms'] / velocity_quant).round() * velocity_quant
    df['vel_q'] = df['vel_q'].clip(lower=min_velocity).astype(int)

    # 4. Reduce to segment boundaries
    df['seg_change'] = df['vel_q'] != df['vel_q'].shift(1)
    waypoints = df[df['seg_change']].copy()
    if df.index[-1] not in waypoints.index:
        waypoints = pd.concat([waypoints, df.iloc[[-1]]])
    waypoints = waypoints.reset_index(drop=True)
    print(f"  Reduced to {len(waypoints)} waypoints ({velocity_quant} mm/s bands)")

    # 5. Flip Z axis
    waypoints['z'] = -waypoints['z']

    # 6. Translate to target origin
    tx, ty, tz = target_origin
    offset_x = tx - waypoints.loc[0, 'x']
    offset_y = ty - waypoints.loc[0, 'y']
    offset_z = tz - waypoints.loc[0, 'z']
    waypoints['x'] += offset_x
    waypoints['y'] += offset_y
    waypoints['z'] += offset_z
    print(f"  Z flipped, translated by ({offset_x:.3f}, {offset_y:.3f}, {offset_z:.3f}) mm")
    print(f"  First waypoint: ({waypoints.loc[0,'x']:.3f}, {waypoints.loc[0,'y']:.3f}, {waypoints.loc[0,'z']:.3f})")
    print(f"  Last  waypoint: ({waypoints.iloc[-1]['x']:.3f}, {waypoints.iloc[-1]['y']:.3f}, {waypoints.iloc[-1]['z']:.3f})")

    # 7. Assign CNT
    n = len(waypoints)
    waypoints['cnt'] = ['FINE' if i == n - 1 else intermediate_cnt for i in range(n)]

    # 8. Build output DataFrame
    for col in ['x', 'y', 'z']:
        waypoints[col] = waypoints[col].round(3)

    out = waypoints[['timestep', 'x', 'y', 'z', 'w', 'p', 'r', 'vel_q', 'cnt']].copy()
    out.columns = ['timestep_ms', 'x', 'y', 'z', 'w', 'p', 'r', 'velocity_mms', 'cnt']
    out.insert(0, 'point_index', range(1, n + 1))

    if output_path:
        out.to_csv(output_path, index=False, sep=';')
        print(f"  Saved preprocessed CSV to '{output_path}'")

    return out


# -- CLI entry point -----------------------------------------------------------

if __name__ == '__main__':
    inp  = sys.argv[1] if len(sys.argv) > 1 else 'path_long.csv'
    outp = sys.argv[2] if len(sys.argv) > 2 else 'traj_preprocessed.csv'
    preprocess(inp, outp)
