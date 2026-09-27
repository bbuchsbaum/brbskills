#!/usr/bin/env python3
"""Stream a local TSV/CSV into a profile, not raw rows. Aggregates may still be sensitive."""
from __future__ import annotations
import argparse, csv, json, math, sys
from pathlib import Path
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent))
from workbench import atomic_write, locked


def profile(path: Path, delimiter: str = "\t", include_labels: bool = False, cap: int = 20) -> dict:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        cols = reader.fieldnames or []
        if not cols or len(set(cols)) != len(cols): raise ValueError("Missing or duplicated header")
        stats = {k: {"missing": 0, "numeric": 0, "nonnumeric": 0, "nonfinite": 0,
                     "min": None, "max": None, "mean": 0.0, "m2": 0.0,
                     "labels": Counter(), "labels_truncated": False} for k in cols}
        n = 0
        for row in reader:
            if None in row or any(v is None for v in row.values()): raise ValueError(f"Malformed row {n+1}")
            n += 1
            for k, raw in row.items():
                v, s = raw.strip(), stats[k]
                if v.lower() in ("", "n/a", "na", "nan", "null"):
                    s["missing"] += 1; continue
                try:
                    x = float(v)
                    if not math.isfinite(x): s["nonfinite"] += 1; continue
                    s["numeric"] += 1
                    s["min"] = x if s["min"] is None else min(s["min"], x)
                    s["max"] = x if s["max"] is None else max(s["max"], x)
                    d = x - s["mean"]; s["mean"] += d / s["numeric"]; s["m2"] += d * (x - s["mean"])
                except ValueError:
                    s["nonnumeric"] += 1
                    if include_labels:
                        if v in s["labels"] or len(s["labels"]) < cap: s["labels"][v] += 1
                        else: s["labels_truncated"] = True
        for s in stats.values():
            m2 = s.pop("m2")
            s["sd"] = max(0, m2 / (s["numeric"]-1)) ** 0.5 if s["numeric"] > 1 else None
            if not s["numeric"]: s["mean"] = None
            if include_labels: s["labels"] = dict(s["labels"])
            else: s.pop("labels"); s.pop("labels_truncated")
    return {"schema_version": "1.0", "source": str(path), "rows": n, "columns": stats,
            "note": "Negative onsets and zero durations may be valid. Timing origin and joins are not certified."}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path); p.add_argument("output", type=Path)
    p.add_argument("--csv", action="store_true"); p.add_argument("--include-labels", action="store_true")
    a = p.parse_args()
    try:
        with locked(a.output):
            if a.output.exists(): raise ValueError("Refusing to overwrite existing profile")
            r = profile(a.input, "," if a.csv else "\t", a.include_labels); atomic_write(a.output, r)
        print(json.dumps({"output": str(a.output), "rows": r["rows"], "ncolumns": len(r["columns"])})); return 0
    except (ValueError, OSError) as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr); return 2
if __name__ == "__main__": raise SystemExit(main())
