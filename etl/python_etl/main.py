import argparse

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
    df = normalize_dataframe(df)
    print(f"Clean rows to load: {len(df)}")

    conn = get_connection(args)
    try:
        load_clean_staging(conn, df)
        upsert_dw(conn)
    finally:
        conn.close()
    print("Python ETL completed.")


def main():
    parser = build_parser()
    run(parser.parse_args())


if __name__ == "__main__":
    main()

