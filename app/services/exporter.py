import csv
from pathlib import Path
from typing import Iterable


def export_csv(path: str, rows: Iterable[dict]) -> None:
    records = list(rows)
    if not records:
        raise ValueError("Aucune donnée à exporter")
    target = Path(path)
    with target.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
