from pathlib import Path

from preprocess_trajectory import preprocess
from preprocess_trajectory import normalize_cnt_value
from ascii_convert_cart import generate_ls_cart
from ascii_convert_joint import ascii_convert
from upload import ftp_upload

# Coordinate transform: first waypoint will land here (mm)
TARGET_ORIGIN = (-10.0, -10.0, -1100.0)

# Velocity quantisation band (mm/s) -- adjust to taste
VELOCITY_QUANT = 5
CNT_VALUE = "CNT100"

RUNTIME_TARGETS = {
    "SIMULATION": ("127.0.0.1", 8),
    "REAL": ("10.147.229.170", 8),
}


def resolve_runtime_target(runtime_target):
    """
    Resolve a runtime target flag into the robot IP and FANUC tool number.
    """

    if not isinstance(runtime_target, str):
        raise ValueError("runtime_target must be 'SIMULATION' or 'REAL'")

    target_key = runtime_target.strip().upper()
    if target_key not in RUNTIME_TARGETS:
        raise ValueError(
            f"Unsupported runtime_target '{runtime_target}'. "
            "Expected 'SIMULATION' or 'REAL'."
        )

    return RUNTIME_TARGETS[target_key]


def run_pipeline(
    RUNTIME_TARGET,
    REMOTE_DIR,
    CSV_FILE,
    LOCAL_LS_FILE,
    PROG_NAME,
    MOVEMENT_TYPE,
    cnt_value=CNT_VALUE,
):
    try:
        runtime_target_key = RUNTIME_TARGET.strip().upper()
        robot_ip, tool_number = resolve_runtime_target(runtime_target_key)
        normalized_cnt_value = normalize_cnt_value(cnt_value)
        local_ls_path = Path(LOCAL_LS_FILE).resolve(strict=False)
        local_ls_path.parent.mkdir(parents=True, exist_ok=True)
        quantized_csv_path = local_ls_path.with_name(f"{local_ls_path.stem}_quantized.csv")
        raw_csv_path = Path(CSV_FILE).resolve(strict=False)

        print("Preprocessing trajectory...")
        waypoints = preprocess(
            input_path=str(raw_csv_path),
            output_path=str(quantized_csv_path),
            target_origin=TARGET_ORIGIN,
            velocity_quant=VELOCITY_QUANT,
            cnt_value=normalized_cnt_value,
        )

        print(f"Generating LS file: {local_ls_path}...")

        if MOVEMENT_TYPE == "CARTESIAN":
            generate_ls_cart(str(local_ls_path), waypoints, PROG_NAME, tool_number=tool_number)
        elif MOVEMENT_TYPE == "JOINT":
            ascii_convert(str(local_ls_path), waypoints, PROG_NAME, tool_number=tool_number)
        else:
            raise ValueError("MOVEMENT_TYPE must be 'CARTESIAN' or 'JOINT'")

        print(f"Uploading to robot at {robot_ip}...")
        ftp_upload(robot_ip, str(local_ls_path), remote_dir=REMOTE_DIR)

        print("Pipeline successfully completed!")
        return {
            "trajectory_id": PROG_NAME,
            "raw_csv_path": str(raw_csv_path),
            "program_name": PROG_NAME,
            "ls_path": str(local_ls_path),
            "quantized_csv_path": str(quantized_csv_path),
            "runtime_target": runtime_target_key,
            "tool_number": tool_number,
            "movement_type": MOVEMENT_TYPE,
            "cnt_value": normalized_cnt_value,
            "remote_dir": REMOTE_DIR,
        }

    except Exception as e:
        print(f"Pipeline failed: {e}")
        raise
