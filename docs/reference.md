# Tham chiếu — đa nền tảng, lệnh lẻ, output

## Môi trường ảo (`.venv`)

```text
python -m venv .venv
```

Kích hoạt: Linux/macOS `source .venv/bin/activate` · Windows cmd `.venv\Scripts\activate.bat` · PowerShell `.venv\Scripts\Activate.ps1`

```text
pip install -r requirements.txt
```

`run.cmd` trên Windows tự dùng `.venv\Scripts\python.exe` nếu thư mục tồn tại (không cần activate khi double-click `run.cmd`).

## Entrypoint thống nhất

Toàn bộ bước schema → ETL → DQ → OLAP → dashboard → predictive do **`run.py`** điều phối. **`run.sh`** (Unix) và **`run.cmd`** (Windows) chỉ gọi `run.py`.

- **Windows:** `python run.py` hoặc `run.cmd` — cần `psql.exe` trong `PATH`.
- **Linux / macOS:** `python3 run.py` hoặc `./run.sh` — cần `psql` trong `PATH`.

Đường dẫn file: dùng dấu ngoặc kép và định dạng đúng OS (`C:\...` hoặc `/home/...`).

## Biến môi trường (PostgreSQL)

| Biến | Mặc định |
|------|-----------|
| `DB_NAME` | `jobmarket` |
| `DB_USER` | `postgres` |
| `DB_HOST` | `localhost` |
| `DB_PORT` | `5432` |
| `DB_PASSWORD` | *(trống)* |

**Linux / macOS (bash):**

```bash
export DB_PASSWORD='secret'
python run.py
```

Hoặc một dòng:

```bash
DB_NAME=jobmarket DB_USER=postgres DB_HOST=localhost DB_PORT=5432 python run.py
```

**Windows — PowerShell:**

```powershell
$env:DB_PASSWORD = "secret"
python run.py
```

**Windows — cmd.exe:**

```bat
set DB_PASSWORD=secret
python run.py
```

## Lệnh thủ công

Dùng `python` hoặc `python3` tùy cài đặt.

**ETL chỉ Python:**

```text
python etl/transform.py --csv-path "/đường/dẫn/jobs_analysis.xlsx" --db-name jobmarket --db-user postgres --db-host localhost --db-port 5432
```

*(Thêm `--db-password` nếu cần.)*

**OLAP / DQ (cần `psql`):**

```text
psql -U postgres -d jobmarket -f analysis/query_olap.sql
psql -U postgres -d jobmarket -f analysis/data_quality_checks.sql
```

**Dashboard ảnh:**

```text
python analysis/dashboard_report.py
```

## UI web demo (Streamlit)

```text
streamlit run web/app.py
```

Tab: Pipeline, Chạy query, Dashboard ảnh.

## Pipeline đầy đủ làm gì (thứ tự)

1. `Schema/create_tables.sql`
2. `Schema/create_index.sql`
3. ETL: `etl/transform.py` → `etl/python_etl/`
4. `analysis/data_quality_checks.sql`
5. `analysis/query_olap.sql`
6. `analysis/dashboard_report.py` → `analysis/output/`
7. `analysis/predictive_prototype.py` → JSON trong `analysis/output/`

## File trong `analysis/output/` (sau khi chạy đủ)

- `dashboard_*.png`, `dashboard_summary.txt`
- `etl_run_summary.json`, `predictive_prototype_report.json`

## Cấu trúc thư mục (tóm tắt)

```text
Schema/     — DDL + index
etl/        — transform.py, python_etl/
analysis/   — OLAP, DQ, dashboard, predictive, output/
web/        — Streamlit demo
docs/       — tài liệu
run.py      — pipeline (mọi OS)
run.sh      — bọ Unix → run.py
run.cmd     — bọ Windows → run.py
requirements.txt
```

Mapping: [requirement_mapping.md](requirement_mapping.md) · Thiết kế: [design_tradeoffs.md](design_tradeoffs.md)
