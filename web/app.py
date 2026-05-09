#!/usr/bin/env python3
"""JobMarket DW — web demo: pipeline wizard + OLAP query runner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg2
import streamlit as st

from query_loader import load_merged_catalog, ordered_groups, repo_root

ROOT = repo_root()


def _predictive_module():
    """Import analysis/predictive_prototype.py (thư mục `analysis` không phải package)."""
    ad = str(ROOT / "analysis")
    if ad not in sys.path:
        sys.path.insert(0, ad)
    import predictive_prototype as pp

    return pp
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
        "Máy chủ (host)",
        value=os.getenv("DB_HOST", "localhost"),
        key="db_host",
    )
    port = st.sidebar.text_input(
        "Cổng (port)",
        value=os.getenv("DB_PORT", "5432"),
        key="db_port",
    )
    db = st.sidebar.text_input(
        "Tên cơ sở dữ liệu",
        value=os.getenv("DB_NAME", "jobmarket"),
        key="db_name",
    )
    user = st.sidebar.text_input(
        "Tài khoản",
        value=os.getenv("DB_USER", "postgres"),
        key="db_user",
    )
    password = st.sidebar.text_input(
        "Mật khẩu",
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

4. **Sau khi có dữ liệu**, tab **Chạy query** (OLAP) hoặc **Dự báo BQ40–43** (chọn từng BQ và tham số).
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


def _df_from_list(rows: list[dict[str, Any]] | None) -> pd.DataFrame | None:
    if not rows:
        return None
    return pd.DataFrame(rows)


PREDICTIVE_BQ_OPTIONS: dict[str, str] = {
    "BQ40 — Dự đoán lương (huấn luyện + nhập tay)": "40",
    "BQ41 — Kỹ năng được săn đón (dự báo, đà tăng, so năm)": "41",
    "BQ42 — Tin tuyển dụng tương đồng nhau": "42",
    "BQ43 — Gợi ý quốc gia / ngành khi có ngân sách & kỹ năng": "43",
    "Bổ sung — Dự báo số lượng tin đăng tháng kế": "extra",
}


def _render_bq40(data: dict[str, Any]) -> None:
    st.subheader("Kết quả BQ40 — Dự đoán mức lương")
    if data.get("error"):
        st.warning(data["error"])
        return
    st.caption(data.get("method_note", ""))
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Số tin trong kho (có lương)", data.get("dataset_rows", "—"))
    c2.metric("Huấn luyện / Kiểm tra", f"{data.get('train_rows', '—')} / {data.get('test_rows', '—')}")
    c3.metric(
        "Sai số trung bình · tuyến tính",
        f"{data.get('mae_linear_regression', 0):,.0f}",
        help="MAE: sai số tuyệt đối trung bình giữa lương thực tế và dự đoán (cùng đơn vị lương).",
    )
    c4.metric(
        "Sai số trung bình · rừng ngẫu nhiên",
        f"{data.get('mae_random_forest', 0):,.0f}",
        help="MAE của mô hình Random Forest.",
    )
    c5.metric(
        "Hệ số R² · tuyến tính / rừng",
        f"{data.get('r2_linear_regression', 0):.3f} / {data.get('r2_random_forest', 0):.3f}",
        help="R² càng gần 1 thì mô hình giải thích được nhiều biến thiên hơn (trên tập kiểm tra).",
    )

    st.markdown(
        "**Bảng mẫu (tập kiểm tra)** — mỗi dòng: đặc điểm tin tuyển, lương thực tế và hai mức dự đoán."
    )
    samp = data.get("sample_predictions") or []
    df = _df_from_list(samp)
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(
            f"Hiển thị tối đa {len(df)} dòng đầu của tập kiểm tra (chi tiết thêm trong mục JSON thô bên dưới)."
        )
    else:
        st.info("Chưa có bảng mẫu — có thể do cache cũ; hãy chạy lại BQ40.")


def _render_bq40_user_prediction(p: dict[str, Any]) -> None:
    st.subheader("Kết quả dự đoán — theo lựa chọn của bạn")
    ins = p.get("thong_so_dau_vao") or {}
    if ins:
        st.markdown("**Đầu vào**")
        st.json(ins)
    c1, c2 = st.columns(2)
    c1.metric(
        "Lương mid dự đoán · hồi quy tuyến tính",
        f"{p.get('du_doan_luong_mid_tuyen_tinh', 0):,.0f}",
    )
    c2.metric(
        "Lương mid dự đoán · rừng ngẫu nhiên",
        f"{p.get('du_doan_luong_mid_rung_ngau_nhien', 0):,.0f}",
    )
    if p.get("method_note"):
        st.caption(p["method_note"])


def _render_bq41(data: dict[str, Any]) -> None:
    st.subheader("Kết quả BQ41 — Kỹ năng được săn đón")
    if data.get("error"):
        st.warning(data["error"])
        return
    st.caption(data.get("method_note", ""))
    t1, t2, t3 = st.tabs(
        ["Dự báo tháng kế", "Đà tăng (3 tháng)", "So sánh theo năm (YoY)"],
    )
    with t1:
        df = _df_from_list(data.get("linear_forecast_next_month_top"))
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Không có dữ liệu.")
    with t2:
        df = _df_from_list(data.get("top_by_momentum_last3m_vs_prev3m"))
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Chưa đủ số tháng để tính đà tăng.")
    with t3:
        df = _df_from_list(data.get("top_by_yoy_demand"))
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Cần ít nhất hai năm dữ liệu để so sánh YoY.")


def _render_bq42(data: dict[str, Any]) -> None:
    st.subheader("Kết quả BQ42 — Tin tương đồng")
    if data.get("error"):
        st.warning(data["error"])
        return
    st.caption(
        f"Mã tin neo: **{data.get('ma_tin_neo', data.get('anchor_fact_job_id', '—'))}** · "
        f"Trọng số thành phần: {data.get('trong_so', data.get('weights'))}"
    )
    df = _df_from_list(data.get("similar_jobs"))
    if df is not None:
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Không có tin tương tự.")


def _render_bq43(data: dict[str, Any]) -> None:
    st.subheader("Kết quả BQ43 — Gợi ý địa điểm & ngành")
    if data.get("error"):
        st.warning(data["error"])
        return
    st.caption(data.get("method_note", ""))
    ins = data.get("tham_so_dau_vao") or data.get("inputs")
    if ins:
        st.markdown("**Tham số đã dùng**")
        st.json(ins)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Quốc gia phù hợp**")
        df = _df_from_list(data.get("quoc_gia_phu_hop") or data.get("best_countries"))
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Không có dữ liệu.")
    with c2:
        st.markdown("**Ngành phù hợp**")
        df = _df_from_list(data.get("nganh_phu_hop") or data.get("best_industries"))
        if df is not None:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Không có dữ liệu.")
    n_match = data.get("so_tin_thoa_dieu_kien", data.get("matching_job_postings", "—"))
    st.caption(f"Số tin thỏa điều kiện lọc: **{n_match}**")


def _render_extra_volume(data: dict[str, Any]) -> None:
    st.subheader("Kết quả bổ sung — Khối lượng tin đăng")
    if data.get("error"):
        st.warning(data["error"])
        return
    st.caption(data.get("method_note", ""))
    val = data.get("so_tin_du_bao_thang_ke", data.get("predicted_next_month_job_count", 0))
    st.metric("Số tin dự báo (tháng kế tiếp)", f"{float(val):,.1f}")


def page_predictive(host: str, port: str, db: str, user: str, password: str):
    st.title("Bước 4 — Dự báo & gợi ý (theo từng BQ)")
    st.caption(
        "Chọn một câu hỏi nghiệp vụ, điền tham số nếu cần, rồi bấm chạy. "
        "Cùng logic với script `analysis/predictive_prototype.py`."
    )
    try:
        pp = _predictive_module()
    except ImportError as e:
        st.error(f"Không import được module dự báo: {e}. Cài `pip install -r requirements.txt`.")
        return

    labels = list(PREDICTIVE_BQ_OPTIONS.keys())
    choice_label = st.selectbox("Chọn câu hỏi (BQ)", labels, key="pred_bq_select")
    bq = PREDICTIVE_BQ_OPTIONS[choice_label]

    if "predictive_by_bq" not in st.session_state:
        st.session_state["predictive_by_bq"] = {}

    run_clicked = False

    if bq == "40":
        st.markdown("#### BQ40 — Dự đoán mức lương")
        st.caption(
            "**Bước 1:** Huấn luyện trên toàn bộ tin có lương trong CSDL (lưu mô hình trong phiên làm việc). "
            "**Bước 2:** Chọn vai trò, hình thức, bằng cấp, quốc gia và số năm kinh nghiệm, rồi dự đoán."
        )
        if st.session_state.get("bq40_lr"):
            st.success("Mô hình đã huấn luyện trong phiên này — bạn có thể bấm **2. Dự đoán lương**.")
        ct1, ct2 = st.columns(2)
        with ct1:
            train40 = st.button("▶ 1. Huấn luyện mô hình", type="primary", key="btn_bq40_train")
        with ct2:
            predict40 = st.button("▶ 2. Dự đoán lương", type="primary", key="btn_bq40_predict")

        opts = st.session_state.get("bq40_dim_options")
        if opts is None:
            roles = ["Unknown"]
            work_types = ["Unknown"]
            qualifications = ["Unknown"]
            countries = ["Unknown"]
            st.info("Chưa tải danh mục từ CSDL. Bấm **1. Huấn luyện mô hình** (lần đầu) để tải vai trò, quốc gia, …")
        else:
            roles = opts["roles"]
            work_types = opts["work_types"]
            qualifications = opts["qualifications"]
            countries = opts["countries"]

        st.markdown("**Thông tin dùng cho dự đoán (bước 2)**")
        r_role = st.selectbox("Vai trò", roles, key="bq40_ui_role")
        r_wt = st.selectbox("Hình thức làm việc", work_types, key="bq40_ui_wt")
        r_q = st.selectbox("Trình độ / bằng cấp", qualifications, key="bq40_ui_q")
        r_c = st.selectbox("Quốc gia", countries, key="bq40_ui_c")
        exp_years = st.number_input(
            "Số năm kinh nghiệm (áp dụng cho cả tối thiểu và tối đa trong mô hình)",
            min_value=0,
            max_value=60,
            value=3,
            step=1,
            key="bq40_ui_exp",
        )

        if train40:
            with st.spinner("Đang huấn luyện mô hình…"):
                try:
                    conn = get_conn(host, port, db, user, password)
                    try:
                        st.session_state["bq40_dim_options"] = pp.salary_dropdown_options(conn)
                        packed = pp.salary_train_models(conn)
                        if packed.get("error"):
                            st.error(packed["error"])
                        else:
                            st.session_state["bq40_lr"] = packed["lr"]
                            st.session_state["bq40_rf"] = packed["rf"]
                            st.session_state["predictive_by_bq"]["40"] = packed["metrics"]
                            st.success("Huấn luyện xong. Bạn có thể bấm **2. Dự đoán lương**.")
                    finally:
                        conn.close()
                except Exception as e:
                    st.exception(e)

        if predict40:
            if "bq40_lr" not in st.session_state:
                st.warning("Chưa có mô hình trong phiên này. Hãy bấm **1. Huấn luyện mô hình** trước.")
            else:
                try:
                    pred = pp.salary_predict_row(
                        st.session_state["bq40_lr"],
                        st.session_state["bq40_rf"],
                        r_role,
                        r_wt,
                        r_q,
                        r_c,
                        int(exp_years),
                        int(exp_years),
                    )
                    st.session_state["bq40_user_prediction"] = pred
                    st.success("Đã dự đoán.")
                except Exception as e:
                    st.exception(e)
    elif bq == "41":
        st.info("**Tham số:** không cần — gom demand skill theo tháng trong DW.")
        run_clicked = st.button("▶ Chạy BQ41", type="primary", key="btn_pred_41")
    elif bq == "42":
        st.markdown("**Tham số BQ42**")
        anchor_raw = st.number_input(
            "`fact_job_id` neo (0 = tự chọn job đầu có skill + lương)",
            min_value=0,
            value=0,
            step=1,
            key="pred_bq42_anchor",
        )
        sim_limit = st.number_input("Số job tương tự tối đa", min_value=1, max_value=100, value=15, key="pred_bq42_limit")
        run_clicked = st.button("▶ Chạy BQ42", type="primary", key="btn_pred_42")
    elif bq == "43":
        st.markdown("**Tham số BQ43**")
        budget_raw = st.number_input(
            "Ngân sách tối đa cho lương mid `(min+max)/2` (0 = median trong DW)",
            min_value=0.0,
            value=0.0,
            step=1000.0,
            format="%.0f",
            key="pred_bq43_budget",
        )
        role_sub = st.text_input(
            "Lọc role / job title (ILIKE, để trống = không lọc)",
            value="",
            key="pred_bq43_role",
        )
        skills_csv = st.text_input(
            "Skills (phân tách dấu phẩy, khớp `dim_skill`)",
            value="python,sql",
            key="pred_bq43_skills",
        )
        run_clicked = st.button("▶ Chạy BQ43", type="primary", key="btn_pred_43")
    else:
        st.info("**Tham số:** không cần — hồi quy theo chuỗi số tin theo tháng.")
        run_clicked = st.button("▶ Chạy Extra", type="primary", key="btn_pred_extra")

    if run_clicked and bq != "40":
        with st.spinner("Đang tính…"):
            try:
                conn = get_conn(host, port, db, user, password)
                try:
                    if bq == "41":
                        out = pp.hot_skills_predict(conn)
                    elif bq == "42":
                        anchor = st.session_state.get("pred_bq42_anchor", 0)
                        lim = int(st.session_state.get("pred_bq42_limit", 15))
                        aid = None if anchor == 0 else int(anchor)
                        if aid is None:
                            aid = pp.pick_default_anchor_fact_job_id(conn)
                        out = (
                            pp.job_similarity(conn, aid, limit=lim)
                            if aid is not None
                            else {"error": "Không có job neo (có skill + lương)."}
                        )
                    elif bq == "43":
                        budget_raw = float(st.session_state.get("pred_bq43_budget", 0.0))
                        role = (st.session_state.get("pred_bq43_role") or "").strip() or None
                        skills = st.session_state.get("pred_bq43_skills", "python,sql")
                        skills_list = [s.strip() for s in str(skills).split(",") if s.strip()]
                        if budget_raw <= 0:
                            med = pd.read_sql(
                                """
                                SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY (min_salary + max_salary) / 2.0) AS m
                                FROM fact_job_posting
                                WHERE min_salary IS NOT NULL AND max_salary IS NOT NULL
                                """,
                                conn,
                            )
                            budget = float(med.iloc[0]["m"] or 0) or 80000.0
                        else:
                            budget = budget_raw
                        out = pp.recruitment_recommend(
                            conn,
                            budget_max_mid_salary=budget,
                            role_substring=role,
                            skill_names=skills_list,
                        )
                    else:
                        out = pp.hiring_trend_forecast(conn)
                finally:
                    conn.close()
                st.session_state["predictive_by_bq"][bq] = out
                st.success("Đã chạy xong.")
            except Exception as e:
                st.exception(e)

    result = st.session_state["predictive_by_bq"].get(bq)
    if bq == "40":
        if result is not None:
            _render_bq40(result)
        up = st.session_state.get("bq40_user_prediction")
        if up:
            _render_bq40_user_prediction(up)
        payload: dict[str, Any] = {}
        if result is not None:
            payload["danh_gia_mo_hinh"] = result
        if up:
            payload["du_doan_theo_nguoi_dung"] = up
        if payload:
            with st.expander("Dữ liệu thô (JSON) — BQ40"):
                st.code(json.dumps(payload, indent=2, default=str), language="json")
    elif result is not None:
        if bq == "41":
            _render_bq41(result)
        elif bq == "42":
            _render_bq42(result)
        elif bq == "43":
            _render_bq43(result)
        else:
            _render_extra_volume(result)
        with st.expander("Dữ liệu thô (JSON) — BQ đang chọn"):
            st.code(json.dumps(result, indent=2, default=str), language="json")

    pred_path = OUTPUT_DIR / "predictive_prototype_report.json"
    if pred_path.is_file():
        st.caption(
            f"Báo cáo JSON đầy đủ từ dòng lệnh: `{pred_path}` "
            f"(chạy `python analysis/predictive_prototype.py` hoặc `python run.py`)."
        )


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
    tab1, tab2, tab3, tab4 = st.tabs(
        ["Pipeline", "Chạy query", "Dashboard ảnh", "Dự báo (BQ40–43)"]
    )

    with tab1:
        page_pipeline(host, port, db, user, password)
    with tab2:
        page_queries(host, port, db, user, password)
    with tab3:
        page_dashboard()
    with tab4:
        page_predictive(host, port, db, user, password)


if __name__ == "__main__":
    main()
