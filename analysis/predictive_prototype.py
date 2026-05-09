#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

import pandas as pd
import psycopg2
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


def get_connection(args):
    return psycopg2.connect(
        dbname=args.db_name,
        user=args.db_user,
        host=args.db_host,
        port=args.db_port,
        password=args.db_password,
    )


def salary_prediction(conn):
    sql = """
    SELECT
        (f.min_salary + f.max_salary) / 2.0 AS target_salary,
        COALESCE(j.role, 'Unknown') AS role,
        COALESCE(wt.work_type_name, 'Unknown') AS work_type,
        COALESCE(q.qualification_name, 'Unknown') AS qualification,
        COALESCE(l.country, 'Unknown') AS country,
        COALESCE(ex.min_years, 0) AS min_exp,
        COALESCE(ex.max_years, 0) AS max_exp
    FROM fact_job_posting f
    JOIN dim_job j ON j.job_id = f.job_id
    JOIN dim_work_type wt ON wt.work_type_id = f.work_type_id
    JOIN dim_qualification q ON q.qualification_id = f.qualification_id
    JOIN dim_experience ex ON ex.experience_id = f.experience_id
    JOIN dim_location l ON l.location_id = f.location_id
    WHERE f.min_salary IS NOT NULL AND f.max_salary IS NOT NULL;
    """
    df = pd.read_sql(sql, conn)
    if len(df) < 100:
        return {"error": f"Not enough rows for robust modeling ({len(df)} rows)."}

    y = df["target_salary"]
    X = df.drop(columns=["target_salary"])
    cat_cols = ["role", "work_type", "qualification", "country"]
    num_cols = ["min_exp", "max_exp"]
    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols),
            ("num", "passthrough", num_cols),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    lr = Pipeline(
        [("prep", preprocessor), ("model", LinearRegression())]
    )
    rf = Pipeline(
        [("prep", preprocessor), ("model", RandomForestRegressor(n_estimators=200, random_state=42))]
    )
    lr.fit(X_train, y_train)
    rf.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    rf_pred = rf.predict(X_test)
    return {
        "dataset_rows": int(len(df)),
        "mae_linear_regression": float(mean_absolute_error(y_test, lr_pred)),
        "mae_random_forest": float(mean_absolute_error(y_test, rf_pred)),
    }


def hot_skills_forecast(conn):
    sql = """
    SELECT
        t.year,
        t.month,
        s.skill_name,
        COUNT(*) AS demand_count
    FROM bridge_job_skill b
    JOIN fact_job_posting f ON f.fact_job_id = b.fact_job_id
    JOIN dim_time t ON t.time_id = f.time_id
    JOIN dim_skill s ON s.skill_id = b.skill_id
    GROUP BY t.year, t.month, s.skill_name
    """
    df = pd.read_sql(sql, conn)
    if df.empty:
        return {"error": "No skill demand rows found."}

    df["period_idx"] = (df["year"] - df["year"].min()) * 12 + df["month"]
    top_skills = (
        df.groupby("skill_name", as_index=False)["demand_count"]
        .sum()
        .sort_values("demand_count", ascending=False)
        .head(10)["skill_name"]
        .tolist()
    )

    forecast_rows = []
    for skill in top_skills:
        d = df[df["skill_name"] == skill]
        if len(d) < 3:
            continue
        model = LinearRegression()
        X = d[["period_idx"]]
        y = d["demand_count"]
        model.fit(X, y)
        next_period = int(df["period_idx"].max() + 1)
        pred = model.predict(pd.DataFrame({"period_idx": [next_period]}))[0]
        forecast_rows.append({"skill_name": skill, "predicted_next_month_demand": max(float(pred), 0.0)})

    return {"top_skill_forecast": sorted(forecast_rows, key=lambda x: x["predicted_next_month_demand"], reverse=True)}


def hiring_trend_forecast(conn):
    sql = """
    SELECT
        t.year,
        t.month,
        COUNT(*) AS job_count
    FROM fact_job_posting f
    JOIN dim_time t ON t.time_id = f.time_id
    GROUP BY t.year, t.month
    ORDER BY t.year, t.month;
    """
    df = pd.read_sql(sql, conn)
    if len(df) < 3:
        return {"error": "Not enough monthly rows for trend forecast."}
    df["period_idx"] = (df["year"] - df["year"].min()) * 12 + df["month"]
    model = LinearRegression()
    model.fit(df[["period_idx"]], df["job_count"])
    next_period = int(df["period_idx"].max() + 1)
    pred = model.predict(pd.DataFrame({"period_idx": [next_period]}))[0]
    return {"predicted_next_month_job_count": max(float(pred), 0.0)}


def build_parser():
    parser = argparse.ArgumentParser(description="Predictive analytics prototype for JobMarket DW")
    parser.add_argument("--db-name", default=os.getenv("DB_NAME", "jobmarket"))
    parser.add_argument("--db-user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--db-host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.getenv("DB_PORT", "5432"))
    parser.add_argument("--db-password", default=os.getenv("DB_PASSWORD"))
    parser.add_argument("--output-dir", default="analysis/output")
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = get_connection(args)
    try:
        report = {
            "bq60_salary_prediction": salary_prediction(conn),
            "bq61_hot_skills_forecast": hot_skills_forecast(conn),
            "bq62_hiring_trend_forecast": hiring_trend_forecast(conn),
        }
    finally:
        conn.close()
    report_path = out_dir / "predictive_prototype_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Predictive prototype report written to: {report_path}")


if __name__ == "__main__":
    main()
