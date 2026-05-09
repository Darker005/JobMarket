import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .clean import normalize_dataframe
from .extract import load_dataset
from .load import get_connection, load_clean_staging, upsert_dw


def build_parser():
    parser = argparse.ArgumentParser(description="Python ETL for JobMarket DW")
    parser.add_argument("--csv-path", required=True, help="Input dataset path (.csv or .xlsx)")
    parser.add_argument("--db-name", default="jobmarket")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-port", default="5432")
    parser.add_argument("--db-password", default=None)
    return parser


def run(args):
    df = load_dataset(args.csv_path)
    input_rows = len(df)
    df = normalize_dataframe(df)
    clean_rows = len(df)
    print(f"Clean rows to load: {clean_rows}")

    conn = get_connection(args)
    try:
        load_clean_staging(conn, df)
        upsert_dw(conn)
    finally:
        conn.close()
    summary = {
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_path": args.csv_path,
        "input_rows": input_rows,
        "loaded_rows": clean_rows,
        "rejected_rows": max(input_rows - clean_rows, 0),
    }
    output_dir = Path("analysis/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "etl_run_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(f"ETL run summary written to {output_dir / 'etl_run_summary.json'}")
    print("Python ETL completed.")


def main():
    parser = build_parser()
    run(parser.parse_args())


if __name__ == "__main__":
    main()

