from __future__ import annotations

import pandas as pd


def align_and_save(df: pd.DataFrame, out_csv_path: str | None = None, out_json_path: str | None = None) -> None:
    """
    Align by date (already ensured upstream), and save to CSV/JSON if paths provided.
    """
    df = df.sort_values("Date")
    if out_csv_path:
        df.to_csv(out_csv_path, index=False)
    if out_json_path:
        df.to_json(out_json_path, orient="records", indent=2)


