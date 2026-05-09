# JobMarket Data Warehouse

Project xây dựng Data Warehouse cho dataset Job Market, gồm:
- Schema dạng star-like (`Schema/create_tables.sql`)
- Index tối ưu truy vấn (`Schema/create_index.sql`)
- ETL bằng Python (module hóa trong `etl/python_etl/`)
- Bộ truy vấn khai thác dữ liệu/OLAP (`analysis/query_olap.sql`)
- Data quality checks sau ETL (`analysis/data_quality_checks.sql`)
- Dashboard/report outputs dạng ảnh (`analysis/dashboard_report.py`)

## 1) Yêu cầu

- PostgreSQL đang chạy (local hoặc remote)
- Python 3.9+
- `pip`

## 2) Cài đặt

```bash
pip install -r requirements.txt
chmod +x run.sh
```

## 3) Chuẩn bị database

Tạo database trước khi chạy (ví dụ):

```bash
createdb -U postgres jobmarket
```

## 4) Chạy toàn bộ pipeline (khuyến nghị)

Trên **Windows**, pipeline thực tế chạy qua Python (cùng logic với Linux), không cần bash:

- Double-click hoặc trong `cmd` / PowerShell: `run.cmd`
- Hoặc: `python run.py` (hoặc `py run.py`)

Cần có **`psql`** trong `PATH` (cài PostgreSQL và thêm thư mục `bin`, ví dụ `...\PostgreSQL\16\bin`). Nếu thiếu, `run.py` sẽ báo lỗi rõ ràng.

Lệnh mặc định trên Linux/macOS:

```bash
./run.sh
```

Hoặc chạy cross-platform bằng Python:

```bash
python run.py
```

Lệnh với file dữ liệu tùy chỉnh (`.csv` hoặc `.xlsx`):

```bash
./run.sh "/duong/dan/toi/jobs_analysis.xlsx"
```

```bash
python run.py --input-path "/duong/dan/toi/jobs_analysis.xlsx"
```

Pipeline `run.sh` sẽ làm:
1. Tạo bảng DW từ `Schema/create_tables.sql`
2. Tạo index từ `Schema/create_index.sql`
3. Chạy Python ETL từ `etl/transform.py` (entrypoint, gọi module trong `etl/python_etl/`)
4. Chạy data quality checks từ `analysis/data_quality_checks.sql`
5. Chạy bộ query OLAP từ `analysis/query_olap.sql`
6. Sinh dashboard/report outputs (PNG + summary) vào `analysis/output/`
7. Chạy predictive prototype và xuất report JSON

## 5) Cấu hình kết nối DB

`run.sh` đọc từ biến môi trường (nếu không có sẽ dùng default):

- `DB_NAME` (default: `jobmarket`)
- `DB_USER` (default: `postgres`)
- `DB_HOST` (default: `localhost`)
- `DB_PORT` (default: `5432`)

Ví dụ:

```bash
DB_NAME=jobmarket DB_USER=postgres DB_HOST=localhost DB_PORT=5432 ./run.sh
```

```bash
DB_NAME=jobmarket DB_USER=postgres DB_HOST=localhost DB_PORT=5432 python run.py
```

## 6) Chạy ETL Python thủ công

Nếu muốn chạy riêng ETL:

```bash
python3 etl/transform.py \
  --csv-path "/home/july/_dev/JobMarket/jobs_analysis.xlsx" \
  --db-name jobmarket \
  --db-user postgres \
  --db-host localhost \
  --db-port 5432
```

## 7) Chạy OLAP thủ công

```bash
psql -U postgres -d jobmarket -f analysis/query_olap.sql
```

## 8) Chạy data quality checks thủ công

```bash
psql -U postgres -d jobmarket -f analysis/data_quality_checks.sql
```

## 9) UI web demo (wizard + danh sách query + chạy từng query)

Cần cài thêm dependency (đã có trong `requirements.txt`):

```bash
pip install -r requirements.txt
```

Chạy Streamlit từ thư mục project:

```bash
streamlit run web/app.py
```

Trình duyệt mở tab **Pipeline** (hướng dẫn + tùy chọn chạy `run.py`), **Chạy query** (chọn OLAP từ `analysis/query_olap.sql` và bấm chạy), **Dashboard ảnh** (xem PNG trong `analysis/output/`).

## 10) Sinh dashboard/report outputs + ảnh chụp output

```bash
python analysis/dashboard_report.py
```

Sau khi chạy, thư mục `analysis/output/` sẽ có:
- `dashboard_jobs_by_month.png`
- `dashboard_top_countries.png`
- `dashboard_top_skills.png`
- `dashboard_salary_by_work_type.png`
- `dashboard_top_industries.png`
- `dashboard_summary.txt`
- `etl_run_summary.json`
- `predictive_prototype_report.json`

## 11) Một số lỗi thường gặp

- **Input path không đúng**
  - Kiểm tra lại đường dẫn truyền vào `./run.sh "...csv"` hoặc `./run.sh "...xlsx"`.
- **Không kết nối được PostgreSQL**
  - Kiểm tra service postgres đang chạy.
  - Kiểm tra `DB_HOST/DB_PORT/DB_USER/DB_NAME`.
- **Thiếu package Python**
  - Chạy lại: `pip install -r requirements.txt`.

## 12) Cấu trúc thư mục chính

```text
Schema/
  create_tables.sql
  create_index.sql
etl/
  transform.py
  python_etl/
    extract.py
    clean.py
    load.py
    main.py
analysis/
  query_olap.sql
  data_quality_checks.sql
  dashboard_report.py
  output/
web/
  app.py
  query_loader.py
docs/
  submission_checklist.md
  design_tradeoffs.md
run.sh
run.py
run.cmd
requirements.txt
```
