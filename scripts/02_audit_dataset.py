from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
import yaml

from imagecas.data.audit import audit_dataset
from imagecas.qc.outliers import flag_outliers


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/imagecas_split1.yaml"))
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts"))
    args = parser.parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    manifest = pd.read_csv(args.manifest)
    audit = audit_dataset(manifest, **config["geometry"])
    outliers = flag_outliers(audit, config["qc"]["tail_cases"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "qc").mkdir(exist_ok=True)
    audit.to_csv(args.output_dir / "data_audit.csv", index=False)
    outliers.to_csv(args.output_dir / "qc" / "outlier_cases.csv", index=False)
    summary = {
        "case_count": len(audit),
        "warning_case_count": int((audit.warning_codes.fillna("") != "").sum()),
        "outlier_case_count": len(outliers),
        "mask_values": sorted(audit.mask_unique_values.unique().tolist()),
    }
    (args.output_dir / "qc" / "audit_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    if summary["warning_case_count"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

