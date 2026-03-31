from pipeline import run_pipeline


# ── CONFIGURATION ─────────────────────────────────────────────────────────

# ── SIMULATION x REAL ─────────────────────────────────────────────────────
ROBOT_IP = '10.147.229.170'   # Real controller (tool_number=8)
# ROBOT_IP       = '127.0.0.1'    # Simulation (tool_number=1)

# ── DIRECTORY ─────────────────────────────────────────────────────
REMOTE_DIR     = 'FR:'

# ── SHORT ─────────────────────────────────────────────────────
CSV_FILE       = '../RL-Trajectory/path_short.csv'
LOCAL_LS_FILE  = 'TRAJSHORT.LS'
PROG_NAME      = 'TRAJSHORT'
run_pipeline(ROBOT_IP, REMOTE_DIR, CSV_FILE, LOCAL_LS_FILE, PROG_NAME)

# ── MEDIUM ─────────────────────────────────────────────────────
CSV_FILE       = '../RL-Trajectory/path_medium.csv'
LOCAL_LS_FILE  = 'TRAJMEDIUM.LS'
PROG_NAME      = 'TRAJMEDIUM'
run_pipeline(ROBOT_IP, REMOTE_DIR, CSV_FILE, LOCAL_LS_FILE, PROG_NAME)

# ── LONG ─────────────────────────────────────────────────────
CSV_FILE       = '../RL-Trajectory/path_long.csv'
LOCAL_LS_FILE  = 'TRAJ1LONG.LS'
PROG_NAME      = 'TRAJ1LONG'
run_pipeline(ROBOT_IP, REMOTE_DIR, CSV_FILE, LOCAL_LS_FILE, PROG_NAME)

print("Starting pipeline...")
