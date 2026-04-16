from pathlib import Path

from pipeline import CNT_VALUE, run_pipeline
from run_manifest import (
    DEFAULT_LS_OUTPUT_DIR,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_MUJOCO_DIR,
    append_prepared_trajectory_record,
    ensure_directory,
    ensure_manifest_parent,
    resolve_or_allocate_trajectory_id,
)


RUNTIME_TARGET = "REAL"
REMOTE_DIR = "FR:"
MOVEMENT_TYPE = "JOINT"


def discover_mujoco_csvs(mujoco_dir=DEFAULT_MUJOCO_DIR):
    mujoco_dir = Path(mujoco_dir)
    if not mujoco_dir.exists():
        raise FileNotFoundError(f"MUJOCO directory not found: {mujoco_dir}")
    return sorted(mujoco_dir.glob("*.csv"))


def prepare_batch(
    runtime_target=RUNTIME_TARGET,
    remote_dir=REMOTE_DIR,
    movement_type=MOVEMENT_TYPE,
    cnt_value=CNT_VALUE,
    mujoco_dir=DEFAULT_MUJOCO_DIR,
    ls_output_dir=DEFAULT_LS_OUTPUT_DIR,
    manifest_path=DEFAULT_MANIFEST_PATH,
):
    ensure_directory(ls_output_dir)
    ensure_manifest_parent(manifest_path)

    prepared_records = []
    for raw_csv_path in discover_mujoco_csvs(mujoco_dir):
        trajectory_id = resolve_or_allocate_trajectory_id(raw_csv_path, manifest_path)
        local_ls_path = Path(ls_output_dir) / f"{trajectory_id}.LS"

        print(f"Preparing {raw_csv_path.name} as {trajectory_id}...")
        artifact = run_pipeline(
            runtime_target,
            remote_dir,
            str(raw_csv_path),
            str(local_ls_path),
            trajectory_id,
            movement_type,
            cnt_value,
        )
        prepared_records.append(append_prepared_trajectory_record(artifact, manifest_path))

    return prepared_records


def main():
    records = prepare_batch()
    print(f"Prepared {len(records)} trajectory program(s).")


if __name__ == "__main__":
    main()
