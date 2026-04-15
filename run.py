#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd, env=None):
    subprocess.run(cmd, check=True, env=env)


def main():
    base_dir = Path(__file__).resolve().parent
    default_input = base_dir / "jobs_analysis.xlsx"

    parser = argparse.ArgumentParser(description="Run full JobMarket DW pipeline")
    parser.add_argument(
        "--input-path",
        default=str(default_input),
        help="Input dataset path (.csv or .xlsx)",
    )
    args = parser.parse_args()

    db_name = os.getenv("DB_NAME", "jobmarket")
    db_user = os.getenv("DB_USER", "postgres")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_password = os.getenv("DB_PASSWORD")

    input_path = Path(args.input_path).expanduser().resolve()
    if not input_path.exists():
        print(f"Loi: Khong tim thay file input tai: {input_path}", file=sys.stderr)
        print("Cach dung: python run.py --input-path /duong/dan/toi/file.csv|file.xlsx", file=sys.stderr)
        sys.exit(1)

    print("------------------------------------------")
    print("Bat dau qua trinh thiet lap Database...")
    print("------------------------------------------")
    print(f"DB: {db_name} ({db_user}@{db_host}:{db_port})")
    print(f"Input: {input_path}")

    env = os.environ.copy()
    if db_password:
        env["PGPASSWORD"] = db_password

    psql_base = [
        "psql",
        "-h",
        db_host,
        "-p",
        db_port,
        "-U",
        db_user,
        "-d",
        db_name,
        "-v",
        "ON_ERROR_STOP=1",
    ]

    print("[1/5] Dang tao schema va index...")
    run_command(psql_base + ["-f", str(base_dir / "Schema" / "create_tables.sql")], env=env)
    run_command(psql_base + ["-f", str(base_dir / "Schema" / "create_index.sql")], env=env)

    print("[2/5] Dang chay Python ETL...")
    etl_cmd = [
        sys.executable,
        str(base_dir / "etl" / "transform.py"),
        "--csv-path",
        str(input_path),
        "--db-name",
        db_name,
        "--db-user",
        db_user,
        "--db-host",
        db_host,
        "--db-port",
        db_port,
    ]
    if db_password:
        etl_cmd.extend(["--db-password", db_password])
    run_command(etl_cmd, env=env)

    print("[3/5] Dang chay data quality checks...")
    run_command(psql_base + ["-f", str(base_dir / "analysis" / "data_quality_checks.sql")], env=env)

    print("[4/5] Dang chay query OLAP...")
    run_command(psql_base + ["-f", str(base_dir / "analysis" / "query_olap.sql")], env=env)

    print("[5/5] Dang tao dashboard/report outputs...")
    dashboard_cmd = [
        sys.executable,
        str(base_dir / "analysis" / "dashboard_report.py"),
        "--db-name",
        db_name,
        "--db-user",
        db_user,
        "--db-host",
        db_host,
        "--db-port",
        db_port,
    ]
    if db_password:
        dashboard_cmd.extend(["--db-password", db_password])
    run_command(dashboard_cmd, env=env)

    print("------------------------------------------")
    print("Hoan thanh thiet lap!")
    print("------------------------------------------")


if __name__ == "__main__":
    main()
