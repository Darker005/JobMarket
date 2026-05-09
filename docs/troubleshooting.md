# Xử lý sự cố

- **Không tìm thấy file input**  
  Dùng đường dẫn tuyệt đối hoặc tương đối đúng OS; `python run.py --input-path "..."`.

- **Không kết nối được PostgreSQL**  
  Firewall / service; đúng `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_NAME`, `DB_PASSWORD` (set theo shell: bash / PowerShell / cmd — xem [reference.md](reference.md)).

- **Thiếu `psql`**  
  Cài PostgreSQL (hoặc chỉ client), thêm `bin` vào `PATH`. Windows: thường `...\PostgreSQL\<version>\bin`.

- **`python` không chạy được (Windows)**  
  Thử `py run.py` hoặc cài Python từ python.org và tick “Add to PATH”.

- **Thiếu package Python**  
  Bật đúng venv (`.venv`) rồi `pip install -r requirements.txt` — hoặc kiểm tra `which python` / `Get-Command python` có trỏ vào `.venv` không.

- **Streamlit / sklearn lỗi import**  
  Cài lại dependency trong đúng môi trường đó.
