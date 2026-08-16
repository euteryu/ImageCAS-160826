from __future__ import annotations

import argparse
import csv
import json
import tempfile
from pathlib import Path

import pandas as pd
import yaml

from imagecas.data.audit import audit_case
from imagecas.data.archives import archive_entries, extract_case
from imagecas.data.discover import sha256_file


def completed_cases(output_csv: Path) -> set[str]:
    if not output_csv.exists() or output_csv.stat().st_size == 0:
        return set()
    return set(pd.read_csv(output_csv, usecols=["case_id"]).case_id)


def append_row(output_csv: Path, row: dict) -> None:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    exists = output_csv.exists() and output_csv.stat().st_size > 0
    with output_csv.open("a", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
        stream.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit multipart ImageCAS archives case by case")
    parser.add_argument(
        "--archive-root", type=Path, default=Path("/kaggle/working/imagecas_archive_links")
    )
    parser.add_argument("--config", type=Path, default=Path("configs/imagecas_split1.yaml"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/data_audit.csv"))
    parser.add_argument("--limit", type=int, help="Audit at most this many not-yet-completed cases")
    parser.add_argument("--no-hashes", action="store_true")
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    completed = completed_cases(args.output)
    archives = sorted(args.archive_root.glob("*.zip"))
    if len(archives) != 5:
        raise RuntimeError(f"Expected five linked archives, found {len(archives)}")

    queue = []
    for archive in archives:
        for case_number, entries in archive_entries(archive).items():
            case_id = f"case{case_number:04d}"
            if case_id not in completed:
                queue.append((case_number, case_id, archive, entries))
    queue.sort(key=lambda item: item[0])
    if args.limit is not None:
        queue = queue[: args.limit]

    print(json.dumps({"already_completed": len(completed), "queued": len(queue)}, indent=2))
    for index, (_, case_id, archive, entries) in enumerate(queue, start=1):
        with tempfile.TemporaryDirectory(prefix=f"imagecas_{case_id}_", dir="/kaggle/working") as tmp:
            image_path, mask_path = extract_case(archive, entries, Path(tmp))
            row = audit_case(case_id, image_path, mask_path, **config["geometry"])
            row["archive"] = archive.name
            row["image_entry"] = entries["img"]
            row["mask_entry"] = entries["label"]
            row["image_sha256"] = "" if args.no_hashes else sha256_file(image_path)
            row["mask_sha256"] = "" if args.no_hashes else sha256_file(mask_path)
            row["image_path"] = entries["img"]
            row["mask_path"] = entries["label"]
            append_row(args.output, row)
        print(f"[{index}/{len(queue)}] {case_id}: {row['warning_codes'] or 'OK'}", flush=True)

    frame = pd.read_csv(args.output).sort_values("case_id")
    frame.to_csv(args.output, index=False)
    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "completed_cases": len(frame),
                "warning_cases": int(frame.warning_codes.fillna("").ne("").sum()),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
