import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = Path(__file__).resolve().parent / "config"
DEFAULT_MANIFEST_PATH = CONFIG_DIR / "run_manifest.jsonl"

TEST_TRAJECTORIES_ROOT = Path(r"K:\Test Trajectories")
DEFAULT_MUJOCO_DIR = TEST_TRAJECTORIES_ROOT / "MUJOCO"
DEFAULT_LS_OUTPUT_DIR = TEST_TRAJECTORIES_ROOT / "LS Programs"
DEFAULT_SIM_RESULTS_DIR = TEST_TRAJECTORIES_ROOT / "ROBOGUIDE"
DEFAULT_REAL_RESULTS_DIR = TEST_TRAJECTORIES_ROOT / "REALDELTA"

RESULT_OUTPUT_DIRS = {
    "SIMULATION": DEFAULT_SIM_RESULTS_DIR,
    "REAL": DEFAULT_REAL_RESULTS_DIR,
}


def utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_path(path_value):
    return str(Path(path_value).resolve(strict=False))


def ensure_directory(directory_path):
    Path(directory_path).mkdir(parents=True, exist_ok=True)


def ensure_manifest_parent(manifest_path=DEFAULT_MANIFEST_PATH):
    ensure_directory(Path(manifest_path).parent)


def load_manifest_records(manifest_path=DEFAULT_MANIFEST_PATH):
    manifest_path = Path(manifest_path)
    if not manifest_path.exists():
        return []

    records = []
    with manifest_path.open("r", encoding="utf-8") as manifest_file:
        for line in manifest_file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def append_manifest_record(record, manifest_path=DEFAULT_MANIFEST_PATH):
    ensure_manifest_parent(manifest_path)
    manifest_path = Path(manifest_path)
    with manifest_path.open("a", encoding="utf-8") as manifest_file:
        manifest_file.write(json.dumps(record, sort_keys=True) + "\n")


def normalize_pair_id(pair_id):
    if not isinstance(pair_id, str) or not pair_id.strip():
        raise ValueError("pair_id must be a non-empty string")
    return pair_id.strip()


def get_result_output_dir(runtime_target):
    target_key = str(runtime_target).strip().upper()
    if target_key not in RESULT_OUTPUT_DIRS:
        raise ValueError("runtime_target must be 'SIMULATION' or 'REAL'")
    return RESULT_OUTPUT_DIRS[target_key]


def _extract_numeric_suffix(value, prefix):
    if not isinstance(value, str) or not value.startswith(prefix):
        return None

    suffix = value[len(prefix):]
    if not suffix.isdigit():
        return None
    return int(suffix)


def allocate_next_trajectory_id(manifest_path=DEFAULT_MANIFEST_PATH):
    max_seen = 0
    for record in load_manifest_records(manifest_path):
        numeric_id = _extract_numeric_suffix(record.get("trajectory_id"), "MJ")
        if numeric_id is not None:
            max_seen = max(max_seen, numeric_id)
    return f"MJ{max_seen + 1:04d}"


def resolve_or_allocate_trajectory_id(raw_csv_path, manifest_path=DEFAULT_MANIFEST_PATH):
    normalized_raw_path = normalize_path(raw_csv_path)

    for record in load_manifest_records(manifest_path):
        if record.get("raw_csv_path") == normalized_raw_path and record.get("trajectory_id"):
            return record["trajectory_id"]

    return allocate_next_trajectory_id(manifest_path)


def allocate_next_run_id(manifest_path=DEFAULT_MANIFEST_PATH):
    max_seen = 0
    for record in load_manifest_records(manifest_path):
        numeric_id = _extract_numeric_suffix(record.get("run_id"), "RUN")
        if numeric_id is not None:
            max_seen = max(max_seen, numeric_id)
    return f"RUN{max_seen + 1:06d}"


def append_prepared_trajectory_record(artifact, manifest_path=DEFAULT_MANIFEST_PATH):
    record = {
        "record_type": "prepared_trajectory",
        "prepared_at_utc": utc_now_iso(),
        "trajectory_id": artifact["trajectory_id"],
        "program_name": artifact["program_name"],
        "raw_csv_path": normalize_path(artifact["raw_csv_path"]),
        "raw_csv_name": Path(artifact["raw_csv_path"]).name,
        "ls_path": normalize_path(artifact["ls_path"]),
        "quantized_csv_path": normalize_path(artifact["quantized_csv_path"]),
        "runtime_target": str(artifact["runtime_target"]).strip().upper(),
        "tool_number": int(artifact["tool_number"]),
        "movement_type": artifact["movement_type"],
        "cnt_value": artifact["cnt_value"],
        "remote_dir": artifact["remote_dir"],
    }
    append_manifest_record(record, manifest_path)
    return record


def lookup_latest_prepared_record(program_name, manifest_path=DEFAULT_MANIFEST_PATH):
    candidates = [
        record
        for record in load_manifest_records(manifest_path)
        if record.get("record_type") == "prepared_trajectory"
        and record.get("program_name") == program_name
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda record: record.get("prepared_at_utc", ""))


def append_captured_run_record(
    program_name,
    pair_id,
    runtime_target,
    result_csv_path,
    manifest_path=DEFAULT_MANIFEST_PATH,
):
    prepared_record = lookup_latest_prepared_record(program_name, manifest_path)
    if prepared_record is None:
        raise ValueError(f"No prepared_trajectory record found for program '{program_name}'.")

    record = {
        "record_type": "captured_run",
        "run_id": allocate_next_run_id(manifest_path),
        "captured_at_utc": utc_now_iso(),
        "pair_id": normalize_pair_id(pair_id),
        "trajectory_id": prepared_record["trajectory_id"],
        "program_name": prepared_record["program_name"],
        "raw_csv_path": prepared_record["raw_csv_path"],
        "ls_path": prepared_record["ls_path"],
        "quantized_csv_path": prepared_record["quantized_csv_path"],
        "runtime_target": str(runtime_target).strip().upper(),
        "result_csv_path": normalize_path(result_csv_path),
        "movement_type": prepared_record["movement_type"],
        "cnt_value": prepared_record["cnt_value"],
    }
    append_manifest_record(record, manifest_path)
    return record


def load_records_by_type(record_type, manifest_path=DEFAULT_MANIFEST_PATH):
    return [
        record
        for record in load_manifest_records(manifest_path)
        if record.get("record_type") == record_type
    ]
