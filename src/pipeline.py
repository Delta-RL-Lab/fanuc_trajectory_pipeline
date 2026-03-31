import numpy as np
from preprocess_trajectory import preprocess
from ascii_convert_cart import generate_ls_cart
from upload import ftp_upload

# Coordinate transform: first waypoint will land here (mm)
TARGET_ORIGIN  = (-10.0, -10.0, -1100.0)

# Velocity quantisation band (mm/s) -- adjust to taste
VELOCITY_QUANT = 5

def run_pipeline(ROBOT_IP, REMOTE_DIR, CSV_FILE, LOCAL_LS_FILE, PROG_NAME):
    try:
        # ── 1. PREPROCESS ─────────────────────────────────────────────────────
        # Loads raw CSV, computes velocities, segments trajectory,
        # flips Z, translates to TARGET_ORIGIN.
        # Returns a DataFrame ready for LS generation.
        print("Preprocessing trajectory...")
        waypoints = preprocess(
            input_path     = CSV_FILE,
            target_origin  = TARGET_ORIGIN,
            velocity_quant = VELOCITY_QUANT,
        )

        # ── 2. GENERATE LS FILE ───────────────────────────────────────────────
        # Writes per-point velocity (mm/s) and CNT/FINE termination from
        # the preprocessed DataFrame directly into the LS motion instructions.
        print(f"Generating LS file: {LOCAL_LS_FILE}...")
        generate_ls_cart(LOCAL_LS_FILE, waypoints, PROG_NAME)

        # ── 3. UPLOAD ─────────────────────────────────────────────────────────
        print(f"Uploading to robot at {ROBOT_IP}...")
        ftp_upload(ROBOT_IP, LOCAL_LS_FILE, remote_dir=REMOTE_DIR)

        print("Pipeline successfully completed!")

    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise
