#!/usr/bin/env python3
"""BQ40–BQ43 + hiring volume: salary model, hot skills, job similarity, recruitment hints."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

_SALARY_SQL = """
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
    WHERE f.min_salary IS NOT NULL AND f.max_salary IS NOT NULL
    """


def get_connection(args):
    return psycopg2.connect(
        dbname=args.db_name,
        user=args.db_user,
        host=args.db_host,
        port=args.db_port,
        password=args.db_password,
    )


def salary_read_training_frame(conn) -> pd.DataFrame:
    return pd.read_sql(_SALARY_SQL, conn)


def salary_dropdown_options(conn) -> dict[str, list[str]]:
    """Giá trị cho selectbox Streamlit (từ chiều DW)."""
    roles = pd.read_sql(
        "SELECT DISTINCT COALESCE(role, 'Unknown') AS v FROM dim_job ORDER BY 1",
        conn,
    )["v"].tolist()
    work_types = pd.read_sql(
        "SELECT DISTINCT work_type_name AS v FROM dim_work_type ORDER BY 1",
        conn,
    )["v"].tolist()
    quals = pd.read_sql(
        "SELECT DISTINCT qualification_name AS v FROM dim_qualification ORDER BY 1",
        conn,
    )["v"].tolist()
    countries = pd.read_sql(
        "SELECT DISTINCT country AS v FROM dim_location ORDER BY 1",
        conn,
    )["v"].tolist()
    out = {
        "roles": roles,
        "work_types": work_types,
        "qualifications": quals,
        "countries": countries,
    }
    for k, v in out.items():
        if not v:
            out[k] = ["Unknown"]
    return out


def salary_train_models(conn) -> dict[str, Any]:
    """
    Huấn luyện hai pipeline (tuyến tính + rừng). Trả về:
    - {'error': ...} hoặc {'metrics': dict (JSON-safe), 'lr': Pipeline, 'rf': Pipeline}
    """
    df = salary_read_training_frame(conn)
    if len(df) < 100:
        return {
            "error": f"Chưa đủ dữ liệu để huấn luyện ổn định (hiện có {len(df)} tin có lương; nên ≥ 100)."
        }

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
    lr = Pipeline([("prep", preprocessor), ("model", LinearRegression())])
    rf = Pipeline(
        [("prep", preprocessor), ("model", RandomForestRegressor(n_estimators=200, random_state=42))]
    )
    lr.fit(X_train, y_train)
    rf.fit(X_train, y_train)
    lr_pred = lr.predict(X_test)
    rf_pred = rf.predict(X_test)

    comparison = X_test.reset_index(drop=True).copy()
    comparison["actual_mid_salary"] = y_test.values.astype(float)
    comparison["pred_linear_regression"] = lr_pred.astype(float)
    comparison["pred_random_forest"] = rf_pred.astype(float)
    comparison["abs_error_linear"] = (comparison["actual_mid_salary"] - comparison["pred_linear_regression"]).abs()
    comparison["abs_error_rf"] = (comparison["actual_mid_salary"] - comparison["pred_random_forest"]).abs()

    sample_n = min(30, len(comparison))
    sample_df = comparison.head(sample_n).round(2)
    sample_df = sample_df.rename(
        columns={
            "role": "Vai trò",
            "work_type": "Hình thức làm việc",
            "qualification": "Trình độ / bằng cấp",
            "country": "Quốc gia",
            "min_exp": "Kinh nghiệm tối thiểu (năm)",
            "max_exp": "Kinh nghiệm tối đa (năm)",
            "actual_mid_salary": "Lương thực tế (trung bình min–max)",
            "pred_linear_regression": "Dự đoán · hồi quy tuyến tính",
            "pred_random_forest": "Dự đoán · rừng ngẫu nhiên",
            "abs_error_linear": "Sai số tuyệt đối · tuyến tính",
            "abs_error_rf": "Sai số tuyệt đối · rừng",
        }
    )

    metrics = {
        "dataset_rows": int(len(df)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "mae_linear_regression": float(mean_absolute_error(y_test, lr_pred)),
        "mae_random_forest": float(mean_absolute_error(y_test, rf_pred)),
        "r2_linear_regression": float(r2_score(y_test, lr_pred)),
        "r2_random_forest": float(r2_score(y_test, rf_pred)),
        "method_note": (
            "Chia dữ liệu: 80% huấn luyện, 20% kiểm tra (cùng seed 42). "
            "Sau khi huấn luyện, dùng nút dự đoán với thông tin bạn chọn. "
            "Bảng mẫu là các dòng trên tập kiểm tra."
        ),
        "sample_predictions": sample_df.to_dict(orient="records"),
    }
    return {"metrics": metrics, "lr": lr, "rf": rf}


def salary_prediction(conn):
    """Chỉ báo cáo đánh giá (CLI / JSON) — không chứa object mô hình."""
    out = salary_train_models(conn)
    if out.get("error"):
        return out
    return out["metrics"]


def salary_predict_row(
    lr: Pipeline,
    rf: Pipeline,
    role: str,
    work_type: str,
    qualification: str,
    country: str,
    min_exp: int,
    max_exp: int,
) -> dict[str, Any]:
    """Một dòng đầu vào → hai mức lương dự đoán (mid)."""
    min_e = max(0, int(min_exp))
    max_e = max(min_e, int(max_exp))
    X = pd.DataFrame(
        [
            {
                "role": role,
                "work_type": work_type,
                "qualification": qualification,
                "country": country,
                "min_exp": min_e,
                "max_exp": max_e,
            }
        ]
    )
    plin = float(lr.predict(X)[0])
    prf = float(rf.predict(X)[0])
    return {
        "thong_so_dau_vao": {
            "Vai trò": role,
            "Hình thức làm việc": work_type,
            "Trình độ / bằng cấp": qualification,
            "Quốc gia": country,
            "Kinh nghiệm tối thiểu (năm)": min_e,
            "Kinh nghiệm tối đa (năm)": max_e,
        },
        "du_doan_luong_mid_tuyen_tinh": round(plin, 2),
        "du_doan_luong_mid_rung_ngau_nhien": round(prf, 2),
        "method_note": "Lương mid = (min_salary + max_salary)/2 trong dữ liệu huấn luyện; đơn vị theo CSDL.",
    }


def _linear_next_month_forecast(df: pd.DataFrame, top_n_volume: int = 20) -> list[dict[str, Any]]:
    """Per-skill OLS on period_idx → demand_count; predict max(period)+1."""
    top_skills = (
        df.groupby("skill_name", as_index=False)["demand_count"]
        .sum()
        .sort_values("demand_count", ascending=False)
        .head(top_n_volume)["skill_name"]
        .tolist()
    )
    next_period = int(df["period_idx"].max() + 1)
    forecast_rows: list[dict[str, Any]] = []
    for skill in top_skills:
        d = df[df["skill_name"] == skill]
        if len(d) < 3:
            continue
        model = LinearRegression()
        model.fit(d[["period_idx"]], d["demand_count"])
        pred = model.predict(pd.DataFrame({"period_idx": [next_period]}))[0]
        forecast_rows.append(
            {
                "Tên kỹ năng": skill,
                "Dự báo nhu cầu tháng kế (số lần gắn vào tin)": round(
                    max(float(pred), 0.0), 2
                ),
            }
        )
    return sorted(
        forecast_rows,
        key=lambda x: x["Dự báo nhu cầu tháng kế (số lần gắn vào tin)"],
        reverse=True,
    )


def hot_skills_predict(conn) -> dict[str, Any]:
    """BQ41: volume forecast + momentum + YoY — không chỉ ‘top skill cũ’."""
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
        return {"error": "Không có dòng nhu cầu kỹ năng theo tháng trong kho dữ liệu."}

    df["period_idx"] = (df["year"] - df["year"].min()) * 12 + df["month"]

    linear_forecast = _linear_next_month_forecast(df, top_n_volume=20)

    momentum_rows: list[dict[str, Any]] = []
    for skill, g in df.groupby("skill_name"):
        g = g.sort_values("period_idx")
        if len(g) < 6:
            continue
        last3 = float(g.tail(3)["demand_count"].mean())
        prev3 = float(g.iloc[-6:-3]["demand_count"].mean())
        if prev3 > 0:
            mom_pct = (last3 - prev3) / prev3 * 100.0
        else:
            mom_pct = 100.0 if last3 > 0 else 0.0
        momentum_rows.append(
            {
                "Tên kỹ năng": skill,
                "Đà tăng so 3 tháng trước (%)": round(mom_pct, 2),
                "Trung bình nhu cầu 3 tháng gần nhất": round(last3, 2),
            }
        )
    momentum_rows = sorted(
        momentum_rows, key=lambda x: x["Đà tăng so 3 tháng trước (%)"], reverse=True
    )[:25]

    yearly = df.groupby(["skill_name", "year"], as_index=False)["demand_count"].sum()
    years = sorted(yearly["year"].unique())
    yoy_rows: list[dict[str, Any]] = []
    if len(years) >= 2:
        y_new, y_old = years[-1], years[-2]
        for skill in yearly["skill_name"].unique():
            a = yearly[(yearly["skill_name"] == skill) & (yearly["year"] == y_new)][
                "demand_count"
            ].sum()
            b = yearly[(yearly["skill_name"] == skill) & (yearly["year"] == y_old)][
                "demand_count"
            ].sum()
            if b and b > 0:
                yoy_rows.append(
                    {
                        "Tên kỹ năng": skill,
                        "Tăng trưởng YoY (%)": round(float((a - b) / b * 100), 2),
                        f"Tổng nhu cầu năm {y_new}": int(a),
                        f"Tổng nhu cầu năm {y_old}": int(b),
                    }
                )
        yoy_rows = sorted(yoy_rows, key=lambda x: x["Tăng trưởng YoY (%)"], reverse=True)[:25]

    return {
        "method_note": (
            "Kỹ năng ‘hot’ gồm: (1) dự báo nhu cầu tháng kế bằng hồi quy theo thời gian, "
            "(2) đà tăng 3 tháng gần so với 3 tháng trước, "
            "(3) so sánh năm mới nhất với năm liền trước nếu có đủ dữ liệu."
        ),
        "linear_forecast_next_month_top": linear_forecast,
        "top_by_momentum_last3m_vs_prev3m": momentum_rows,
        "top_by_yoy_demand": yoy_rows,
    }


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
        return {
            "error": "Chưa đủ số tháng để dự báo xu hướng (cần ít nhất 3 tháng có tin)."
        }
    df["period_idx"] = (df["year"] - df["year"].min()) * 12 + df["month"]
    model = LinearRegression()
    model.fit(df[["period_idx"]], df["job_count"])
    next_period = int(df["period_idx"].max() + 1)
    pred = model.predict(pd.DataFrame({"period_idx": [next_period]}))[0]
    return {
        "so_tin_du_bao_thang_ke": max(float(pred), 0.0),
        "method_note": "Ước lượng số tin đăng tuyển ở tháng kế tiếp dựa trên chuỗi số tin theo tháng (hồi quy tuyến tính).",
    }


def pick_default_anchor_fact_job_id(conn) -> int | None:
    q = """
    SELECT f.fact_job_id
    FROM fact_job_posting f
    WHERE EXISTS (SELECT 1 FROM bridge_job_skill b WHERE b.fact_job_id = f.fact_job_id)
      AND f.min_salary IS NOT NULL AND f.max_salary IS NOT NULL
    ORDER BY f.fact_job_id
    LIMIT 1;
    """
    row = pd.read_sql(q, conn)
    if row.empty:
        return None
    return int(row.iloc[0]["fact_job_id"])


def job_similarity(conn, anchor_fact_job_id: int, limit: int = 15) -> dict[str, Any]:
    """BQ42: Jaccard(skill) + role match + salary proximity."""
    sql = """
    WITH anchor_role AS (
        SELECT COALESCE(j.role, '') AS role,
               (f.min_salary + f.max_salary) / 2.0 AS mid_sal
        FROM fact_job_posting f
        JOIN dim_job j ON j.job_id = f.job_id
        WHERE f.fact_job_id = %s
    ),
    anchor_sk AS (
        SELECT skill_id FROM bridge_job_skill WHERE fact_job_id = %s
    ),
    anchor_cnt AS (
        SELECT COUNT(*)::double precision AS cnt FROM anchor_sk
    ),
    cand AS (
        SELECT
            f.fact_job_id,
            j.job_title,
            COALESCE(j.role, '') AS role,
            (f.min_salary + f.max_salary) / 2.0 AS mid_sal,
            COUNT(b.skill_id) AS n_b,
            COUNT(b.skill_id) FILTER (WHERE b.skill_id IN (SELECT skill_id FROM anchor_sk)) AS inter
        FROM fact_job_posting f
        JOIN dim_job j ON j.job_id = f.job_id
        JOIN bridge_job_skill b ON b.fact_job_id = f.fact_job_id
        WHERE f.fact_job_id <> %s
          AND f.min_salary IS NOT NULL AND f.max_salary IS NOT NULL
        GROUP BY f.fact_job_id, j.job_title, j.role, f.min_salary, f.max_salary
        HAVING COUNT(b.skill_id) FILTER (WHERE b.skill_id IN (SELECT skill_id FROM anchor_sk)) > 0
    )
    SELECT
        c.fact_job_id,
        c.job_title,
        c.role,
        c.mid_sal,
        c.inter::int AS shared_skills,
        c.n_b::int AS candidate_skill_count,
        (SELECT cnt FROM anchor_cnt) AS anchor_skill_count,
        (c.inter / NULLIF((SELECT cnt FROM anchor_cnt) + c.n_b - c.inter, 0))::double precision AS jaccard_skills,
        CASE WHEN c.role = (SELECT role FROM anchor_role) THEN 1.0 ELSE 0.0 END AS role_match,
        (
            1.0 - LEAST(
                1.0,
                ABS(c.mid_sal - (SELECT mid_sal FROM anchor_role))
                / NULLIF(GREATEST(ABS((SELECT mid_sal FROM anchor_role)), c.mid_sal), 0)
            )
        )::double precision AS salary_similarity
    FROM cand c
    ORDER BY
        (c.inter / NULLIF((SELECT cnt FROM anchor_cnt) + c.n_b - c.inter, 0)) DESC,
        salary_similarity DESC
    LIMIT %s;
    """
    df = pd.read_sql(sql, conn, params=(anchor_fact_job_id, anchor_fact_job_id, anchor_fact_job_id, limit))
    if df.empty:
        return {
            "ma_tin_neo": anchor_fact_job_id,
            "error": "Không có tin tương tự (cần ít nhất một kỹ năng trùng và tin có khoảng lương).",
            "similar_jobs": [],
        }
    w_j, w_r, w_s = 0.5, 0.3, 0.2
    df["similarity_score"] = (
        w_j * df["jaccard_skills"] + w_r * df["role_match"] + w_s * df["salary_similarity"]
    )
    df = df.sort_values("similarity_score", ascending=False)
    df = df.rename(
        columns={
            "fact_job_id": "Mã tin tuyển dụng",
            "job_title": "Tên công việc",
            "role": "Vai trò",
            "mid_sal": "Lương trung bình (min–max)",
            "shared_skills": "Số kỹ năng trùng",
            "candidate_skill_count": "Tổng kỹ năng (tin ứng viên)",
            "anchor_skill_count": "Tổng kỹ năng (tin neo)",
            "jaccard_skills": "Độ trùng kỹ năng (Jaccard)",
            "role_match": "Trùng vai trò (1=có)",
            "salary_similarity": "Độ gần mức lương (0–1)",
            "similarity_score": "Điểm tương đồng tổng hợp",
        }
    )
    records = df.to_dict(orient="records")
    for r in records:
        r["Điểm tương đồng tổng hợp"] = round(float(r["Điểm tương đồng tổng hợp"]), 4)
        for k in ("Độ trùng kỹ năng (Jaccard)", "Độ gần mức lương (0–1)", "Lương trung bình (min–max)"):
            if k in r and r[k] is not None:
                r[k] = float(r[k])
    return {
        "ma_tin_neo": anchor_fact_job_id,
        "trong_so": {
            "Trùng kỹ năng (Jaccard)": w_j,
            "Trùng vai trò": w_r,
            "Gần mức lương": w_s,
        },
        "similar_jobs": records,
    }


def recruitment_recommend(
    conn,
    budget_max_mid_salary: float,
    role_substring: str | None,
    skill_names: list[str],
    top_n: int = 10,
) -> dict[str, Any]:
    """BQ43: gợi ý country / industry theo ngân sách lương (mid), role, overlap skill."""
    names = [s.strip().lower() for s in skill_names if s.strip()]
    if not names:
        return {"error": "Cần ít nhất một skill (tên như trong dim_skill)."}

    q_sk = """
    SELECT skill_id, skill_name FROM dim_skill
    WHERE LOWER(TRIM(skill_name)) IN %s
    """
    dim_sk = pd.read_sql(q_sk, conn, params=(tuple(names),))
    if dim_sk.empty:
        return {
            "error": "Không khớp tên kỹ năng nào trong danh mục kỹ năng (bảng dim_skill).",
            "ten_ky_nang_ban_nhap": names,
        }

    skill_ids = dim_sk["skill_id"].astype(int).tolist()
    id_list = ",".join(str(i) for i in skill_ids)

    role_clause = ""
    params: list[Any] = [budget_max_mid_salary]
    if role_substring and role_substring.strip():
        role_clause = " AND (j.role ILIKE %s OR j.job_title ILIKE %s)"
        pat = f"%{role_substring.strip()}%"
        params.extend([pat, pat])

    base_sql = f"""
    SELECT
        f.fact_job_id,
        l.country,
        COALESCE(c.industry, 'Unknown') AS industry,
        (f.min_salary + f.max_salary) / 2.0 AS mid_sal,
        (
            SELECT COUNT(*)::int FROM bridge_job_skill b
            WHERE b.fact_job_id = f.fact_job_id AND b.skill_id IN ({id_list})
        ) AS overlap_cnt
    FROM fact_job_posting f
    JOIN dim_location l ON l.location_id = f.location_id
    JOIN dim_company c ON c.company_id = f.company_id
    JOIN dim_job j ON j.job_id = f.job_id
    WHERE f.min_salary IS NOT NULL AND f.max_salary IS NOT NULL
      AND (f.min_salary + f.max_salary) / 2.0 <= %s
      {role_clause}
    """
    hits = pd.read_sql(base_sql, conn, params=params)
    hits = hits[hits["overlap_cnt"] > 0]
    if hits.empty:
        return {
            "error": "Không có tin thỏa điều kiện: lương mid ≤ ngân sách và trùng kỹ năng"
            + (" và khớp vai trò/tiêu đề." if role_clause else "."),
            "ky_nang_da_khop_trong_kho": dim_sk["skill_name"].tolist(),
            "ngan_sach_luong_mid_da_dung": budget_max_mid_salary,
        }

    by_country = (
        hits.groupby("country", as_index=False)
        .agg(
            job_count=("fact_job_id", "count"),
            skill_overlap_sum=("overlap_cnt", "sum"),
            avg_mid_salary=("mid_sal", "mean"),
        )
        .sort_values("skill_overlap_sum", ascending=False)
        .head(top_n)
        .rename(
            columns={
                "country": "Quốc gia",
                "job_count": "Số tin tuyển",
                "skill_overlap_sum": "Tổng điểm trùng kỹ năng",
                "avg_mid_salary": "Lương mid trung bình",
            }
        )
    )
    by_ind = (
        hits.groupby("industry", as_index=False)
        .agg(
            job_count=("fact_job_id", "count"),
            skill_overlap_sum=("overlap_cnt", "sum"),
            avg_mid_salary=("mid_sal", "mean"),
        )
        .sort_values("skill_overlap_sum", ascending=False)
        .head(top_n)
        .rename(
            columns={
                "industry": "Ngành",
                "job_count": "Số tin tuyển",
                "skill_overlap_sum": "Tổng điểm trùng kỹ năng",
                "avg_mid_salary": "Lương mid trung bình",
            }
        )
    )

    return {
        "method_note": (
            "Lọc các tin có lương mid không vượt ngân sách và trùng ít nhất một kỹ năng bạn chọn; "
            "xếp hạng quốc gia / ngành theo tổng điểm trùng kỹ năng (ưu tiên nhiều skill khớp)."
        ),
        "tham_so_dau_vao": {
            "Ngân sách lương mid tối đa": budget_max_mid_salary,
            "Lọc vai trò hoặc tiêu đề (tùy chọn)": role_substring,
            "Danh sách kỹ năng bạn nhập": skill_names,
            "Kỹ năng khớp trong kho dữ liệu": dim_sk["skill_name"].tolist(),
        },
        "quoc_gia_phu_hop": by_country.to_dict(orient="records"),
        "nganh_phu_hop": by_ind.to_dict(orient="records"),
        "so_tin_thoa_dieu_kien": int(len(hits)),
    }


def build_predictive_report(
    conn,
    *,
    anchor_fact_job_id: int | None = None,
    rec_budget: float | None = None,
    rec_role: str | None = None,
    rec_skills_csv: str = "python,sql",
    similarity_limit: int = 15,
) -> dict[str, Any]:
    """Gom BQ40–BQ43 + hiring volume; dùng cho CLI và Streamlit (cùng logic)."""
    anchor = anchor_fact_job_id
    if anchor is None:
        anchor = pick_default_anchor_fact_job_id(conn)

    budget = rec_budget
    if budget is None:
        med = pd.read_sql(
            """
            SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY (min_salary + max_salary) / 2.0) AS m
            FROM fact_job_posting
            WHERE min_salary IS NOT NULL AND max_salary IS NOT NULL
            """,
            conn,
        )
        budget = float(med.iloc[0]["m"] or 0) or 80000.0

    skills_list = [s.strip() for s in rec_skills_csv.split(",") if s.strip()]

    return {
        "bq40_salary_prediction": salary_prediction(conn),
        "bq41_hot_skills": hot_skills_predict(conn),
        "bq42_job_similarity": job_similarity(conn, anchor, limit=similarity_limit)
        if anchor is not None
        else {"error": "Không có fact_job_id neo (không tìm thấy job có skill + lương)."},
        "bq43_recruitment_recommendation": recruitment_recommend(
            conn,
            budget_max_mid_salary=budget,
            role_substring=rec_role,
            skill_names=skills_list,
        ),
        "extra_hiring_volume_forecast": hiring_trend_forecast(conn),
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Predictive analytics BQ40–BQ43 for JobMarket DW")
    parser.add_argument("--db-name", default=os.getenv("DB_NAME", "jobmarket"))
    parser.add_argument("--db-user", default=os.getenv("DB_USER", "postgres"))
    parser.add_argument("--db-host", default=os.getenv("DB_HOST", "localhost"))
    parser.add_argument("--db-port", default=os.getenv("DB_PORT", "5432"))
    parser.add_argument("--db-password", default=os.getenv("DB_PASSWORD"))
    parser.add_argument("--output-dir", default="analysis/output")
    parser.add_argument(
        "--anchor-fact-job-id",
        type=int,
        default=None,
        help="BQ42: fact_job_id neo cho similarity (mặc định: job đầu có skill + lương).",
    )
    parser.add_argument(
        "--rec-budget",
        type=float,
        default=None,
        help="BQ43: ngân sách lương tối đa (mid = (min+max)/2). Mặc định: median mid trong DW.",
    )
    parser.add_argument("--rec-role", default=None, help="BQ43: lọc role/title ILIKE %%value%%")
    parser.add_argument(
        "--rec-skills",
        default="python,sql",
        help="BQ43: danh sách skill phân tách dấu phẩy (khớp dim_skill, không phân biệt hoa thường).",
    )
    return parser


def main():
    args = build_parser().parse_args()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = get_connection(args)
    try:
        report = build_predictive_report(
            conn,
            anchor_fact_job_id=args.anchor_fact_job_id,
            rec_budget=args.rec_budget,
            rec_role=args.rec_role,
            rec_skills_csv=args.rec_skills,
        )
    finally:
        conn.close()
    report_path = out_dir / "predictive_prototype_report.json"
    report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"Predictive prototype report written to: {report_path}")


if __name__ == "__main__":
    main()
