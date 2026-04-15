#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import matplotlib.pyplot as plt
import psycopg2


def get_connection(args):
    return psycopg2.connect(
        dbname=args.db_name,
        user=args.db_user,
        host=args.db_host,
        port=args.db_port,
        password=args.db_password,
    )


def fetch_rows(conn, query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


def chart_jobs_by_month(conn, output_dir: Path):
    rows = fetch_rows(
        conn,
        """
        SELECT t.year, t.month, COUNT(*) AS total_jobs
        FROM fact_job f
        JOIN dim_time t ON t.time_id = f.time_id
        GROUP BY t.year, t.month
        ORDER BY t.year, t.month;
        """,
    )
    labels = [f"{y}-{m:02d}" for y, m, _ in rows]
    values = [c for _, _, c in rows]

    plt.figure(figsize=(12, 5))
    plt.plot(labels, values, marker="o", linewidth=2)
    plt.xticks(rotation=45, ha="right")
    plt.title("Job Postings by Month")
    plt.xlabel("Year-Month")
    plt.ylabel("Total Jobs")
    plt.tight_layout()
    plt.savefig(output_dir / "dashboard_jobs_by_month.png", dpi=150)
    plt.close()


def chart_top_countries(conn, output_dir: Path):
    rows = fetch_rows(
        conn,
        """
        SELECT l.country, COUNT(*) AS total_jobs
        FROM fact_job f
        JOIN dim_location l ON l.location_id = f.location_id
        GROUP BY l.country
        ORDER BY total_jobs DESC
        LIMIT 10;
        """,
    )
    countries = [r[0] for r in rows]
    values = [r[1] for r in rows]

    plt.figure(figsize=(10, 6))
    plt.barh(countries[::-1], values[::-1])
    plt.title("Top 10 Countries by Job Count")
    plt.xlabel("Total Jobs")
    plt.ylabel("Country")
    plt.tight_layout()
    plt.savefig(output_dir / "dashboard_top_countries.png", dpi=150)
    plt.close()


def chart_top_skills(conn, output_dir: Path):
    rows = fetch_rows(
        conn,
        """
        SELECT s.skill_name, COUNT(*) AS jobs_requiring_skill
        FROM bridge_job_skill b
        JOIN dim_skill s ON s.skill_id = b.skill_id
        GROUP BY s.skill_name
        ORDER BY jobs_requiring_skill DESC
        LIMIT 10;
        """,
    )
    skills = [r[0] for r in rows]
    values = [r[1] for r in rows]

    plt.figure(figsize=(12, 6))
    plt.bar(skills, values)
    plt.xticks(rotation=40, ha="right")
    plt.title("Top 10 Skills by Demand")
    plt.xlabel("Skill")
    plt.ylabel("Jobs Requiring Skill")
    plt.tight_layout()
    plt.savefig(output_dir / "dashboard_top_skills.png", dpi=150)
    plt.close()


def write_summary_report(conn, output_dir: Path):
    rows = fetch_rows(
        conn,
        """
        SELECT
          COUNT(*) AS total_jobs,
          COUNT(DISTINCT company_id) AS total_companies,
          COUNT(DISTINCT location_id) AS total_locations,
          AVG((min_salary + max_salary) / 2.0) AS avg_mid_salary
        FROM fact_job;
        """,
    )
    total_jobs, total_companies, total_locations, avg_mid_salary = rows[0]
    report_path = output_dir / "dashboard_summary.txt"
    report_path.write_text(
        "\n".join(
            [
                "JobMarket DW Dashboard Summary",
                "================================",
                f"Total jobs: {total_jobs}",
                f"Total companies: {total_companies}",
                f"Total locations: {total_locations}",
                f"Average mid salary: {avg_mid_salary:.2f}" if avg_mid_salary else "Average mid salary: N/A",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser():
    parser = argparse.ArgumentParser(description="Generate dashboard/report images from JobMarket DW")
    parser.add_argument("--db-name", default=os.getenv("DB_NAME", "jobmarket"))
    parser.add_argument("--db-user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--db-host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.getenv("DB_PORT", "5432"))
    parser.add_argument("--db-password", default=os.getenv("DB_PASSWORD"))
    parser.add_argument(
        "--output-dir",
        default="analysis/output",
        help="Directory to save generated report images and summary",
    )
    return parser


def main():
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    conn = get_connection(args)
    try:
        chart_jobs_by_month(conn, output_dir)
        chart_top_countries(conn, output_dir)
        chart_top_skills(conn, output_dir)
        write_summary_report(conn, output_dir)
    finally:
        conn.close()

    print(f"Dashboard/report outputs written to: {output_dir}")


if __name__ == "__main__":
    main()
