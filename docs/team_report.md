# Team Report - JobMarket Data Warehouse

Tài liệu này mô tả dự án theo đúng 7 bước chuẩn Data Warehouse, viết chi tiết để người mới có thể học lại từ đầu.

## 1) Hiểu bài toán (Business Understanding)

### Bài toán nghiệp vụ
Dữ liệu đầu vào là các tin tuyển dụng (job postings). Mục tiêu là xây dựng kho dữ liệu để trả lời các câu hỏi phân tích:

- Thị trường tuyển dụng tăng/giảm theo tháng, quý, năm ra sao?
- Quốc gia/thành phố nào có nhiều việc làm nhất?
- Kỹ năng nào được yêu cầu nhiều nhất?
- Mức lương trung bình theo portal, loại công việc, trình độ có khác nhau không?

### Vì sao cần Data Warehouse
Hệ thống giao dịch (OLTP) không tối ưu cho phân tích tổng hợp trên nhiều chiều dữ liệu. Data Warehouse giúp:

- Tổ chức dữ liệu theo mô hình phân tích (fact/dimension).
- Truy vấn OLAP nhanh hơn và rõ ràng hơn.
- Làm nền tảng cho dashboard/report.

## 2) Thiết kế Logical (Star Schema)

Dự án dùng mô hình **star-like** với 1 fact trung tâm và các dimension bao quanh.

### 2.1 Các bảng logical đã thiết kế

- `fact_job`: bảng fact chính, chứa số đo và khóa tham chiếu đến các dimension.
- `dim_time`: chiều thời gian.
- `dim_location`: chiều địa lý.
- `dim_company`: chiều công ty.
- `dim_job`: chiều thông tin công việc.
- `dim_portal`: chiều kênh đăng tuyển.
- `dim_preference`: chiều loại hình ưu tiên/ưu đãi.
- `dim_skill`: chiều kỹ năng.
- `bridge_job_skill`: bảng nối nhiều-nhiều giữa `fact_job` và `dim_skill`.

### 2.2 Grain (mức chi tiết) của fact
Grain được chọn là: **1 dòng trong `fact_job` = 1 job posting (theo `job_id`) tại thời điểm đăng tin**.

Đây là điểm rất quan trọng vì mọi truy vấn OLAP và quy tắc ETL đều phải bám theo grain này.

### 2.3 Vì sao tạo mô hình như vậy

- Tối ưu cho truy vấn tổng hợp (COUNT, AVG, GROUP BY) theo nhiều chiều.
- Dễ mở rộng dashboard/report.
- Dễ dạy, dễ học, đúng tinh thần bài tập Data Warehouse cơ bản.

## 3) Thiết kế Physical (Database Schema)

Phần physical được hiện thực trong:

- `Schema/create_tables.sql`
- `Schema/create_index.sql`

### 3.1 Cụ thể từng bảng và lý do tạo

1. `dim_time`  
   - Cột chính: `time_id`, `full_date`, `day`, `month`, `year`, `quarter`.  
   - Lý do: chiều thời gian luôn là chiều quan trọng nhất trong DW để làm trend, drill-down theo năm/quý/tháng.

2. `dim_location`  
   - Cột chính: `location_id`, `city`, `country`, `latitude`, `longitude`.  
   - Lý do: phân tích địa lý và hỗ trợ bản đồ/heatmap.

3. `dim_company`  
   - Cột chính: `company_id`, `company_name`, `company_size`, `sector`, `industry`, `city`, `state`.  
   - Lý do: phân tích theo doanh nghiệp, quy mô, ngành.

4. `dim_job`  
   - Cột chính: `job_dim_id`, `job_title`, `role`, `work_type`, `qualification`.  
   - Lý do: gom các thuộc tính nghiệp vụ của vị trí công việc để phân tích nhu cầu tuyển dụng.

5. `dim_portal`  
   - Cột chính: `portal_id`, `portal_name`.  
   - Lý do: đo hiệu quả theo nguồn/kênh đăng tuyển.

6. `dim_preference`  
   - Cột chính: `preference_id`, `preference_name`.  
   - Lý do: hỗ trợ phân tích theo điều kiện ưu tiên trong tin tuyển dụng.

7. `dim_skill`  
   - Cột chính: `skill_id`, `skill_name`.  
   - Lý do: tách kỹ năng thành dimension riêng để làm top skill, skill vs salary.

8. `fact_job`  
   - Cột chính: `fact_job_id`, `job_id`, các FK tới dimension, và các measure như `min_salary`, `max_salary`, `min_experience_years`, `max_experience_years`.  
   - Lý do: đây là trung tâm phân tích, chứa số đo + ngữ cảnh theo dimension.

9. `bridge_job_skill`  
   - Cột chính: (`fact_job_id`, `skill_id`).  
   - Lý do: quan hệ giữa job và skill là nhiều-nhiều, không thể nhét trực tiếp vào `fact_job` nếu muốn phân tích chuẩn.

### 3.2 Index đã tạo và lý do

Trong `Schema/create_index.sql` đã tạo index trên các FK của `fact_job`:

- `time_id`, `location_id`, `company_id`, `job_dim_id`, `portal_id`, `preference_id`
- và index `skill_id` cho `bridge_job_skill`

Lý do: tăng tốc join fact-dimension trong các truy vấn OLAP.

### 3.3 Điểm cần lưu ý ở physical

- `job_id` trong `fact_job` đang để `UNIQUE` => mô hình hiện tại giả định một job_id chỉ có một bản ghi fact.
- `dim_company` đang unique theo `company_name`, có thể gặp trường hợp trùng tên công ty ở nhiều nơi.
- Dự án chưa dùng partition và chưa làm SCD Type 2 (đã nêu trong `docs/design_tradeoffs.md`).

## 4) Import dữ liệu -> Staging (Step-by-step)

Đây là phần rất quan trọng để hiểu ETL chạy như thế nào.

### Bước 4.1 - Đọc dữ liệu nguồn
- File: `etl/python_etl/extract.py`
- Hỗ trợ `.xlsx`, `.xls`, `.csv`
- Đọc toàn bộ dưới dạng text trước để dễ chuẩn hóa.

### Bước 4.2 - Chuẩn hóa và làm sạch
- File: `etl/python_etl/clean.py`
- Các xử lý chính:
  - Đổi tên cột nguồn sang tên cột chuẩn nội bộ.
  - Parse `job_id` sang số.
  - Parse ngày đăng tin `posting_date`.
  - Parse `min_salary`, `max_salary`, `latitude`, `longitude`.
  - Parse range kinh nghiệm từ chuỗi.
  - Parse JSON `company_profile` để tách `sector`, `industry`, `company_city`, `company_state`.
  - Loại các dòng thiếu cột bắt buộc hoặc dữ liệu không hợp lệ.

### Bước 4.3 - Nạp vào staging table
- File: `etl/python_etl/load.py`
- Tạo bảng tạm `stg_jobs_clean`, sau đó bulk load bằng `COPY`.

### Vì sao cần staging

- Tách rõ “làm sạch dữ liệu” và “nạp vào DW”.
- Dễ kiểm tra khi ETL lỗi.
- Giảm độ phức tạp khi map sang dimension/fact.

## 5) ETL (Transform + Load vào DW) - Step-by-step

### Bước 5.1 - Upsert dimension
Từ `stg_jobs_clean`, ETL insert distinct vào:

- `dim_time`
- `dim_location`
- `dim_company`
- `dim_job`
- `dim_portal`
- `dim_preference`

Dùng `ON CONFLICT DO NOTHING` để tránh trùng dữ liệu.

### Bước 5.2 - Nạp fact
Join staging với các dimension để lấy khóa surrogate, sau đó insert vào `fact_job`.

### Bước 5.3 - Xử lý skill nhiều-nhiều

- Tách chuỗi `skills_raw` thành từng skill.
- Nạp skill vào `dim_skill`.
- Nối `fact_job` với `dim_skill` qua `bridge_job_skill`.

### Bước 5.4 - Kiểm tra chất lượng dữ liệu sau ETL
- File: `analysis/data_quality_checks.sql`
- Gồm:
  - Row counts từng bảng.
  - Null checks cột bắt buộc.
  - Domain checks (min <= max với salary/experience).
  - Referential checks (orphan FK phải bằng 0).
  - Bridge integrity checks.
  - Duplicate checks theo business key.

## 6) Khai thác dữ liệu (Query, OLAP)

File chính: `analysis/query_olap.sql`

### Các nhóm truy vấn đã làm

- Trend theo thời gian (năm/tháng/quý).
- Phân tích địa lý (country/city).
- Phân tích theo thuộc tính công việc (`job_title`, `work_type`, `qualification`).
- Phân tích theo nguồn tuyển dụng (`portal`, `preference`).
- Phân tích kỹ năng (top skills, salary theo skill).
- OLAP thao tác đa chiều:
  - Slice
  - Dice
  - Drilldown

### Tối ưu cho truy vấn báo cáo
Đã tạo materialized view `mv_jobs_country_month` để pre-aggregate dữ liệu.

## 7) Report (SSRS / Dashboard)

### Report đã triển khai trong dự án

- Script: `analysis/dashboard_report.py`
- Output tại: `analysis/output/`

### Ảnh/report sinh ra

- `dashboard_jobs_by_month.png`
- `dashboard_top_countries.png`
- `dashboard_top_skills.png`
- `dashboard_summary.txt`

Đây là bản dashboard tự động bằng Python, tương đương mức report cơ bản cho đồ án.

Nếu cần tiến gần hơn SSRS/SSAS:
- Kết nối DB này vào Power BI/Metabase/Tableau/Pentaho để có dashboard tương tác.

## Quy trình chạy toàn bộ hệ thống (end-to-end)

Chạy một lệnh:

```bash
./run.sh
```

hoặc:

```bash
python run.py --input-path "/đường/dẫn/tới/jobs_analysis.xlsx"
```

Pipeline hiện tại chạy theo thứ tự:

1. Tạo bảng và index (`create_tables.sql`, `create_index.sql`)
2. Chạy ETL Python (`extract -> clean -> staging -> load DW`)
3. Chạy data quality checks (`data_quality_checks.sql`)
4. Chạy OLAP queries (`query_olap.sql`)
5. Sinh dashboard/report outputs (`dashboard_report.py`)

## Những điểm cần chú ý khi học và trình bày

- Luôn nói rõ grain của fact trước khi nói query.
- Giải thích vì sao có `bridge_job_skill` (nhiều-nhiều).
- Nhấn mạnh staging là điểm tách quan trọng trong ETL.
- Trình bày data quality checks để chứng minh dữ liệu đáng tin cậy.
- Nêu trade-off rõ ràng:
  - Chọn star-like để đơn giản và tối ưu phân tích.
  - Chưa làm SCD/partition ở phiên bản này do phạm vi đồ án.

## Kết luận

Project đã hoàn thiện một quy trình Data Warehouse có thể chạy end-to-end:

- Có mô hình logical + physical rõ ràng
- Có ETL với staging
- Có kiểm thử chất lượng dữ liệu sau ETL
- Có khai thác OLAP
- Có report/dashboard output

Ở mức học phần, đây là một hệ thống DW hoàn chỉnh và đủ tốt để báo cáo, demo, và học lại kiến trúc chuẩn của DW.
