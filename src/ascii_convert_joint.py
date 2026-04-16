"""
ascii_convert_joint.py
----------------------
Generates a FANUC .LS ASCII teach-pendant program that reuses the
preprocessed Cartesian waypoint table, but emits JOINT motion commands.

The trajectory data itself is preserved from preprocess_trajectory:
  - Cartesian P[...] records are written directly from x/y/z/w/p/r.
  - Per-point velocity_mms values are scaled to FANUC joint percentages.
  - CNT/FINE termination terms are read from the existing 'cnt' column.
"""

import numpy as np


def _scale_joint_percentages(waypoints_df):
    """
    Scale the existing velocity_mms profile into FANUC joint percentages.

    The maximum velocity in the file maps to 100%, with all other points
    scaled proportionally and clamped into the valid 1..100 range.
    """

    velocities = np.asarray(waypoints_df["velocity_mms"], dtype=float)
    if velocities.size == 0:
        return np.array([], dtype=int)

    max_velocity = np.nanmax(velocities)
    if not np.isfinite(max_velocity) or max_velocity <= 0:
        return np.ones_like(velocities, dtype=int)

    scaled = np.rint((velocities / max_velocity) * 100.0)
    return np.clip(scaled, 1, 100).astype(int)


def ascii_convert(filename, waypoints_df, prog_name="TRAJ1", tool_number=8):
    """
    Write a FANUC .LS motion program that uses J instructions while keeping
    Cartesian position records.

    Parameters
    ----------
    filename : str
        Output .LS file path.
    waypoints_df : pd.DataFrame
        Preprocessed waypoint table with columns:
            point_index, timestep_ms, x, y, z, w, p, r,
            velocity_mms, cnt
    prog_name : str
        Program name written into the LS header and /PROG line.
    tool_number : int
        FANUC tool number written into the Cartesian position records.
    """

    required_columns = {
        "point_index",
        "x",
        "y",
        "z",
        "w",
        "p",
        "r",
        "velocity_mms",
        "cnt",
    }
    missing = required_columns - set(waypoints_df.columns)
    if missing:
        raise ValueError(f"Waypoint DataFrame is missing columns: {sorted(missing)}")

    n_points = len(waypoints_df)
    line_count = n_points + 4
    config_string = "'F, , 0, 0'"
    joint_percentages = _scale_joint_percentages(waypoints_df)

    with open(filename, "w") as f:
        f.write(f"/PROG  {prog_name}\n")
        f.write("/ATTR\n")
        f.write("OWNER\t\t= MNEDITOR;\n")
        f.write('COMMENT\t\t= "Generated";\n')
        f.write("PROG_SIZE\t= 0;\n")
        f.write(f"FILE_NAME\t= {prog_name};\n")
        f.write("VERSION\t\t= 0;\n")
        f.write(f"LINE_COUNT\t= {line_count};\n")
        f.write("MEMORY_SIZE\t= 0;\n")
        f.write("PROTECT\t\t= READ_WRITE;\n")
        f.write(
            "TCD:  STACK_SIZE\t= 0,\n"
            "      TASK_PRIORITY\t= 50,\n"
            "      TIME_SLICE\t= 0,\n"
            "      BUSY_LAMP_OFF\t= 0,\n"
            "      ABORT_REQUEST\t= 0,\n"
            "      PAUSE_REQUEST\t= 0;\n"
        )
        f.write("DEFAULT_GROUP\t= 1,*,*,*,*;\n")
        f.write("CONTROL_CODE\t= 00000000 00000000;\n")
        f.write("/APPL\n")
        f.write("/MN\n")

        f.write("   1:  J P[1] 100% FINE        ;\n")
        f.write("   2:  WAIT 10.00(sec)    ;\n")
        f.write("   3:  TIMER[1]=RESET    ;\n")
        f.write("   4:  TIMER[1]=START    ;\n")

        for speed_percent, (_, row) in zip(joint_percentages, waypoints_df.iterrows()):
            line_no = int(row["point_index"]) + 4
            pt_no = int(row["point_index"])
            term = row["cnt"]
            f.write(f"   {line_no}:J P[{pt_no}] {speed_percent}% {term}    ;\n")

        f.write(f"   {n_points + 5}:  TIMER[1]=STOP    ;\n")
        f.write(f"   {n_points + 6}:  END    ;\n")

        f.write("/POS\n")

        for _, row in waypoints_df.iterrows():
            pt_no = int(row["point_index"])
            x, y, z = row["x"], row["y"], row["z"]
            w, p, r = row["w"], row["p"], row["r"]

            f.write(f"P[{pt_no}]{{\n")
            f.write("   GP1:\n")
            f.write(f"\tUF : 0, UT : {tool_number},\t\tCONFIG : {config_string},\n")
            f.write(
                f"\tX = {x:10.3f}  mm,\tY = {y:10.3f}  mm,\tZ = {z:10.3f}  mm,\n"
            )
            f.write(f"\tW = {w:10.3f} deg,\tP = {p:10.3f} deg,\tR = {r:10.3f} deg\n")
            f.write("};\n")

        f.write("/END\n")

    print(f"  Written {n_points} points to '{filename}'")
