import argparse
import json
from pathlib import Path
import sys

from summary import summarize


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input")
    parser.add_argument("--backend", choices=("demo", "file"), default="file")
    args = parser.parse_args()
    try:
        values = [1, 2, 3] if args.backend == "demo" else json.loads(Path(args.input).read_text())
        print(json.dumps(summarize(values)))
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
