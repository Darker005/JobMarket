#!/usr/bin/env python3
"""JobMarket DW — web demo: pipeline wizard + OLAP query runner."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
import psycopg2
import streamlit as st

from query_loader import load_merged_catalog, ordered_groups, repo_root

ROOT = repo_root()
OLAP_SQL = ROOT / "analysis" / "query_olap.sql"
BQ_GAPS_SQL = ROOT / "analysis" / "query_bq_gaps.sql"
OUTPUT_DIR = ROOT / "analysis" / "output"
DEFAULT_INPUT = ROOT / "jobs_analysis.xlsx"


def get_conn(host: str, port: str, db: str, user: str, password: str | None):
    return psycopg2.connect(
        host=host,
        port=port,
        dbname=db,
        user=user,
        password=password or None,
    )


def run_sql(conn, sql: str) -> pd.DataFrame:
    return pd.read_sql_query(sql, conn)


def sidebar_db():
    st.sidebar.header("Kết nối PostgreSQL")
    host = st.sidebar.text_input(
        "Host",
        value=os.getenv("DB_HOST", "localhost"),
        key="db_host",
    )
    port = st.sidebar.text_input(
        "Port",
        value=os.getenv("DB_PORT", "5432"),
        key="db_port",
    )
    db = st.sidebar.text_input(
        "Database",
        value=os.getenv("DB_NAME", "jobmarket"),
        key="db_name",
    )
    user = st.sidebar.text_input(
        "User",
        value=os.getenv("DB_USER", "postgres"),
        key="db_user",
    )
    password = st.sidebar.text_input(
        "Password",
        type="password",
        value=os.getenv("DB_PASSWORD") or "",
        key="db_password",
    )
    return host, port, db, user, password


def page_pipeline(host: str, port: str, db: str, user: str, password: str):
    st.title("Bước 1 — Pipeline từ đầu đến cuối")
    st.markdown(
        """
1. **Cài dependency:** `pip install -r requirements.txt`
2. **Tạo database:** `createdb -U postgres jobmarket` (hoặc tương đương)
3. **Chạy pipeline đầy đủ** (schema → ETL → DQ → OLAP file → dashboard → predictive):

   ```bash
   python run.py
   ```

   Hoặc chỉ định file dữ liệu:

   ```bash
   python run.py --input-path /path/to/jobs_analysis.xlsx
   ```

4. **Sau khi có dữ liệu**, sang tab **Chạy query** để bấm từng câu OLAP.
        """
    )

    st.subheader("Chạy pipeline từ UI (tùy chọn)")
    st.caption("Chạy `run.py` trên máy bạn; cần `psql` trong PATH và Python đủ package.")
    input_path = st.text_input("Đường dẫn file input", value=str(DEFAULT_INPUT), key="pipeline_input")
    if st.button("▶ Chạy toàn bộ pipeline (`python run.py`)", type="primary", key="btn_run_pipeline"):
        env = os.environ.copy()
        env.setdefault("DB_HOST", host)
        env.setdefault("DB_PORT", port)
        env.setdefault("DB_NAME", db)
        env.setdefault("DB_USER", user)
        if password:
            env["DB_PASSWORD"] = password
        cmd = [sys.executable, str(ROOT / "run.py"), "--input-path", input_path]
        with st.spinner("Đang chạy pipeline… (có thể vài phút)"):
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(ROOT),
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=3600,
                )
                st.code(proc.stdout or "(no stdout)", language="text")
                if proc.stderr:
                    st.code(proc.stderr, language="text")
                if proc.returncode != 0:
                    st.error(f"Thoát mã {proc.returncode}")
                else:
                    st.success("Pipeline hoàn tất.")
            except subprocess.TimeoutExpired:
                st.error("Timeout.")
            except Exception as e:
                st.exception(e)

    st.subheader("Kiểm tra kết nối DB")
    if st.button("Thử kết nối", key="btn_test_conn"):
        try:
            conn = get_conn(host, port, db, user, password)
            conn.close()
            st.success("Kết nối OK.")
        except Exception as e:
            st.error(str(e))


def page_queries(host: str, port: str, db: str, user: str, password: str):
    st.title("Bước 2 — Danh sách truy vấn phân tích")
    st.caption("Mỗi mục thuộc một **nhóm nghiệp vụ**, kèm **tên gọi** và **mục đích sử dụng** — không gắn nhãn Phase A/B/C trong giao diện.")
    if not OLAP_SQL.is_file():
        st.error(f"Không tìm thấy {OLAP_SQL}")
        return

    sql_paths = [OLAP_SQL]
    if BQ_GAPS_SQL.is_file():
        sql_paths.append(BQ_GAPS_SQL)
    queries = load_merged_catalog(sql_paths)
    olap_only = [q for q in queries if q["kind"] == "olap"]
    ddl_only = [q for q in queries if q["kind"] == "ddl"]

    olap_groups = ordered_groups({q["group"] for q in olap_only})
    maintenance_token = "⛭ Bảo trì CSDL (materialized view & index)"
    group_choices = ["Tất cả nhóm (phân tích)"] + olap_groups + [maintenance_token]

    group_sel = st.selectbox("Lọc theo nhóm", group_choices, key="q_group")

    if group_sel == maintenance_token:
        filtered = ddl_only
    elif group_sel == "Tất cả nhóm (phân tích)":
        filtered = olap_only
    else:
        filtered = [q for q in olap_only if q["group"] == group_sel]

    options = {
        f"{q['name']} · #{q['id']}": q
        for q in filtered
    }
    if not options:
        st.warning("Không có truy vấn nào sau lọc.")
        return

    choice = st.selectbox("Chọn truy vấn", list(options.keys()), key="q_choice")
    q = options[choice]

    st.markdown(f"**Nhóm:** {q['group']}")
    st.markdown(f"**Tên:** {q['name']}")
    st.markdown(f"**Dùng để:** {q['purpose']}")

    with st.expander("Xem SQL"):
        st.code(q["sql"], language="sql")

    limit_rows = st.number_input(
        "Giới hạn số dòng hiển thị (0 = không giới hạn; chỉ áp dụng truy vấn trả bảng)",
        min_value=0,
        value=5000,
        key="q_limit",
    )

    if st.button("▶ Chạy truy vấn này", type="primary", key="btn_run_query"):
        try:
            conn = get_conn(host, port, db, user, password)
            try:
                if q["kind"] == "ddl":
                    with conn.cursor() as cur:
                        cur.execute(q["sql"])
                    conn.commit()
                    st.success("Đã thực thi lệnh DDL.")
                else:
                    df = run_sql(conn, q["sql"])
                    if limit_rows and len(df) > limit_rows:
                        st.warning(f"Chỉ hiển thị {limit_rows}/{len(df)} dòng.")
                        df = df.head(limit_rows)
                    st.dataframe(df, use_container_width=True)
                    st.caption(f"{len(df)} dòng (sau giới hạn hiển thị nếu có).")
            finally:
                conn.close()
        except Exception as e:
            st.error(str(e))


def page_dashboard():
    st.title("Bước 3 — Ảnh dashboard (sau khi chạy pipeline)")
    if not OUTPUT_DIR.is_dir():
        st.warning(f"Chưa có thư mục {OUTPUT_DIR}")
        return
    images = sorted(OUTPUT_DIR.glob("*.png"))
    if not images:
        st.info("Chưa có file PNG. Chạy `python run.py` hoặc `python analysis/dashboard_report.py`.")
        return
    for img in images:
        st.subheader(img.name)
        st.image(str(img), use_container_width=True)


def main():
    st.set_page_config(page_title="JobMarket DW Demo", layout="wide")
    host, port, db, user, password = sidebar_db()
    tab1, tab2, tab3 = st.tabs(["Pipeline", "Chạy query", "Dashboard ảnh"])

    with tab1:
        page_pipeline(host, port, db, user, password)
    with tab2:
        page_queries(host, port, db, user, password)
    with tab3:
        page_dashboard()


if __name__ == "__main__":
    main()
