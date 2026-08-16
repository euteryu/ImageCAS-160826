from __future__ import annotations

import pandas as pd


def flag_outliers(audit: pd.DataFrame, tail_n: int = 10) -> pd.DataFrame:
    flags: dict[str, set[str]] = {}
    def add(case_ids, reason):
        for case_id in case_ids:
            flags.setdefault(case_id, set()).add(reason)
    warnings = audit[audit.warning_codes.fillna("") != ""]
    for row in warnings.itertuples():
        add([row.case_id], row.warning_codes)
    for column in ["foreground_fraction", "connected_component_count", "image_p01", "image_p99"]:
        ordered = audit.sort_values(column)
        add(ordered.head(tail_n).case_id, f"LOW_{column.upper()}")
        add(ordered.tail(tail_n).case_id, f"HIGH_{column.upper()}")
    return pd.DataFrame(
        [{"case_id": case_id, "outlier_reasons": ";".join(sorted(reasons))} for case_id, reasons in sorted(flags.items())]
    )

