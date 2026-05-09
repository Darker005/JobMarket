# JobMarket Data Warehouse

Pipeline **đa nền tảng** (Windows, Linux, macOS): **PostgreSQL** + **Python** → OLAP / DQ / dashboard / prototype. Cùng một logic pipeline trong `run.py` — shell chỉ là lớp bọ mỏng.

Chi tiết: [docs/reference.md](docs/reference.md) · Sự cố: [docs/troubleshooting.md](docs/troubleshooting.md)

## Yêu cầu

- PostgreSQL (server + **`psql`** trong `PATH` để chạy file `.sql`)
- Python **3.9+** (kèm `pip` / `venv`)

## Môi trường ảo Python (khuyến nghị)

Dùng thư mục **`.venv`** trong gốc repo (trùng với `run.cmd` trên Windows — nếu có `.venv` thì `run.cmd` ưu tiên interpreter đó).

**1. Tạo env** (từ thư mục gốc project):

```text
python -m venv .venv
```

*(Nếu máy chỉ có `python3`: `python3 -m venv .venv`.)*

**2. Kích hoạt**

| Hệ điều hành | Lệnh |
|---------------|------|
| Linux / macOS | `source .venv/bin/activate` |
| Windows (cmd) | `.venv\Scripts\activate.bat` |
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |

*(PowerShell: nếu bị chặn script, chạy một lần `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.)*

**3. Cài package (trong env đã bật)**

```text
pip install -r requirements.txt
```

**4. Thoát env** (khi xong): `deactivate`

Sau bước này mọi lệnh `python run.py`, `streamlit run web/app.py`, v.v. đều dùng đúng interpreter trong `.venv`.

## Tạo database

**Linux / macOS** (client `createdb`):

```bash
createdb -U postgres jobmarket
```

**Windows** (PowerShell / `cmd`, sau khi `psql` có trong PATH):

```text
psql -U postgres -c "CREATE DATABASE jobmarket;"
```

Hoặc tạo DB bằng pgAdmin / bất kỳ công cụ nào — chỉ cần đúng tên DB khi set `DB_NAME`.

## Chạy pipeline (mọi OS — khuyến nghị)

Từ thư mục gốc repo:

```text
python run.py
```

File input khác:

```text
python run.py --input-path "C:\path\to\file.xlsx"
```

```text
python run.py --input-path "/home/user/file.xlsx"
```

### Lớp bọ tùy chọn (cùng hành vi với `run.py`)

| Hệ điều hành | Lệnh |
|---------------|------|
| Windows | `run.cmd` hoặc `python run.py` |
| Linux / macOS | `python run.py` hoặc `./run.sh` *(cần `chmod +x run.sh` lần đầu)* |

Biến môi trường `DB_*`: xem [docs/reference.md](docs/reference.md).

## Demo web (Streamlit)

```text
streamlit run web/app.py
```

---

*Thiết kế: [docs/design_tradeoffs.md](docs/design_tradeoffs.md) · Mapping dữ liệu: [docs/requirement_mapping.md](docs/requirement_mapping.md)*
