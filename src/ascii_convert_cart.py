"""
ascii_convert_cart.py
---------------------
Generates a FANUC .LS ASCII teach-pendant program from a preprocessed
waypoint DataFrame (output of preprocess_trajectory.preprocess()).

Key differences from the original version:
  - Accepts a DataFrame instead of a raw numpy array.
  - Positions are already in mm and degrees -- no unit conversion applied.
  - Per-point velocity (mm/s) and CNT termination type are read from the
    DataFrame columns 'velocity_mms' and 'cnt'.
  - CNT column accepts 'FINE', 'CNT0' .. 'CNT100'  (any valid FANUC term).
"""

import numpy as np


def generate_ls_cart(filename, waypoints_df, prog_name='TRAJ1'):
    """
    Write a FANUC .LS Cartesian motion program.

    Parameters
    ----------
    filename : str
        Output .LS file path.
    waypoints_df : pd.DataFrame
        Preprocessed waypoint table with columns:
            point_index, timestep_ms, x, y, z, w, p, r,
            velocity_mms, cnt
        Positions in mm, orientations in degrees.
    prog_name : str
        Program name written into the LS header and /PROG line.
    """

    n_points = len(waypoints_df)

    # Total instruction lines: TIMER RESET + TIMER START + n motion lines
    #                          + TIMER STOP + END  =  n + 4
    line_count = n_points + 4

    config_string = "'F, , 0, 0'"
    
    tool_number = 8 # 8 for real
    # tool_number = 1 # 1 for simulation (ROBOGUIDE)

    with open(filename, 'w') as f:

        # ── HEADER ────────────────────────────────────────────────────────────
        f.write(f"/PROG  {prog_name}\n")
        f.write("/ATTR\n")
        f.write("OWNER\t\t= MNEDITOR;\n")
        f.write("COMMENT\t\t= \"Generated\";\n")
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

        # ── MOTION INSTRUCTIONS ───────────────────────────────────────────────
        f.write("   1:  L P[1] 50mm/sec FINE        ;\n")
        f.write("   2:  WAIT 10.00(sec)    ;\n")
        f.write("   3:  TIMER[1]=RESET    ;\n")
        f.write("   4:  TIMER[1]=START    ;\n")

        for idx, row in waypoints_df.iterrows():
            line_no  = row['point_index'] + 4          # offset by 2 header lines
            pt_no    = int(row['point_index'])
            velocity = int(row['velocity_mms'])
            term     = row['cnt']                       # e.g. 'FINE', 'CNT100'
            f.write(f"   {line_no}:L P[{pt_no}] {velocity}mm/sec {term}    ;\n")

        f.write(f"   {n_points + 5}:  TIMER[1]=STOP    ;\n")
        f.write(f"   {n_points + 6}:  END    ;\n")

        # ── POSITION RECORDS ─────────────────────────────────────────────────
        f.write("/POS\n")

        for _, row in waypoints_df.iterrows():
            pt_no = int(row['point_index'])
            x, y, z = row['x'], row['y'], row['z']
            w, p, r = row['w'], row['p'], row['r']

            f.write(f"P[{pt_no}]{{\n")
            f.write("   GP1:\n")
            f.write(f"\tUF : 0, UT : {tool_number},\t\tCONFIG : {config_string},\n")
            f.write(f"\tX = {x:10.3f}  mm,\tY = {y:10.3f}  mm,\tZ = {z:10.3f}  mm,\n")
            f.write(f"\tW = {w:10.3f} deg,\tP = {p:10.3f} deg,\tR = {r:10.3f} deg\n")
            f.write("};\n")

        f.write("/END\n")

    print(f"  Written {n_points} points to '{filename}'")
