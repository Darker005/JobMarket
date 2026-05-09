#!/bin/bash
set -euo pipefail

# --- CẤU HÌNH DATABASE ---
DB_NAME="${DB_NAME:-jobmarket}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Đường dẫn đến thư mục project
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
# Input file path can be passed as first argument; supports .csv/.xlsx.
CSV_PATH="${1:-$BASE_DIR/jobs_analysis.xlsx}"

echo "------------------------------------------"
echo "Bắt đầu quá trình thiết lập Database..."
echo "------------------------------------------"
echo "DB: $DB_NAME ($DB_USER@$DB_HOST:$DB_PORT)"
echo "CSV: $CSV_PATH"

# Kiểm tra file CSV tồn tại
if [[ ! -f "$CSV_PATH" ]]; then
  echo "Loi: Khong tim thay file CSV tai: $CSV_PATH"
  echo "Cach dung: ./run.sh '/duong/dan/toi/file.csv|file.xlsx'"
  exit 1
fi

# 1) Create schema + indexes
echo "[1/6] Dang tao schema va index..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 \
  -f "$BASE_DIR/Schema/create_tables.sql"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 \
  -f "$BASE_DIR/Schema/create_index.sql"

# 2) Run Python ETL
echo "[2/6] Dang chay Python ETL..."
python3 "$BASE_DIR/etl/transform.py" \
  --csv-path "$CSV_PATH" \
  --db-name "$DB_NAME" \
  --db-user "$DB_USER" \
  --db-host "$DB_HOST" \
  --db-port "$DB_PORT"

# 3) Run data quality checks
echo "[3/6] Dang chay data quality checks..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -f "$BASE_DIR/analysis/data_quality_checks.sql"

# 4) Run OLAP queries
echo "[4/6] Dang chay query OLAP..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
  -v ON_ERROR_STOP=1 \
  -f "$BASE_DIR/analysis/query_olap.sql"

# 5) Generate dashboard/report outputs
echo "[5/6] Dang tao dashboard/report outputs..."
python3 "$BASE_DIR/analysis/dashboard_report.py" \
  --db-name "$DB_NAME" \
  --db-user "$DB_USER" \
  --db-host "$DB_HOST" \
  --db-port "$DB_PORT"

# 6) Run predictive prototype
echo "[6/6] Dang chay predictive prototype..."
python3 "$BASE_DIR/analysis/predictive_prototype.py" \
  --db-name "$DB_NAME" \
  --db-user "$DB_USER" \
  --db-host "$DB_HOST" \
  --db-port "$DB_PORT"

echo "------------------------------------------"
echo "Hoàn thành thiết lập!"
echo "------------------------------------------"
