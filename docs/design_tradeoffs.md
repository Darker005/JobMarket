# Design Trade-offs (Current Version)

Tai lieu nay dung de giai thich cac quyet dinh thiet ke trong phien ban hien tai cua JobMarket DW.

## 1) Vi sao chon star-like schema

Chung toi chon mo hinh star-like voi `fact_job` o trung tam va cac bang dimension (`dim_time`, `dim_location`, `dim_company`, `dim_job`, `dim_portal`, `dim_preference`) vi:

- Truy van phan tich (OLAP) de viet, de doc, de giang day.
- Hieu nang tot cho nhom query tong hop va group-by tren fact lon.
- De tich hop vao dashboard/reporting tools (Power BI, Metabase, Tableau).
- Phu hop voi scope do an mon hoc: can ETL + query + bao cao, uu tien implementation nhanh.

Han che da chap nhan:

- Mot so dimension co do du thua thong tin cao hon so voi snowflake.
- Chua model hoa hierarchy phuc tap (alternative/non-strict) bang nhieu bang dimension cap cao.

## 2) Vi sao chua dung SCD trong phien ban nay

Trong phien ban hien tai, dimensions duoc nap theo hinh thuc "upsert basic", chua co SCD Type 2.

Ly do:

- Du lieu dau vao chu yeu la snapshot-style job postings, khong cung cap ro lich su thay doi thuoc tinh dimension theo thoi diem.
- Muc tieu do an uu tien pipeline on dinh va kha nang query.
- Giam do phuc tap ETL (effective_date, end_date, current_flag, dedup logic).

Rui ro/han che:

- Neu thuoc tinh dimension thay doi theo thoi gian (vd: company size, industry), he thong chua luu duoc lich su day du theo ban ghi dimension.

Huong mo rong:

- Bo sung SCD Type 2 cho `dim_company` va (neu can) `dim_job`.
- Them cot `effective_from`, `effective_to`, `is_current`, va doi join logic fact -> dim theo business key + thoi gian.

## 3) Vi sao chua partition trong phien ban nay

Partitioning chua duoc ap dung o phien ban hien tai.

Ly do:

- Kich thuoc dataset mon hoc chua du lon de partition tao khac biet ro rang.
- Tang chi phi van hanh (partition key strategy, maintenance, query plan tuning).
- Hien tai da co index FK + materialized view phuc vu dashboard cho hieu nang co ban.

Rui ro/han che:

- Khi du lieu tang manh theo thoi gian, mot so query quet toan bang fact se cham hon.

Huong mo rong:

- Partition `fact_job` theo `time_id` (thang/quy/nam), ket hop pruning.
- Dat lich refresh MV dinh ky sau ETL.

## 4) Ket luan scope ky thuat hien tai

Phien ban hien tai dat muc tieu do an o muc "functional DW":

- ETL -> staging -> dimension/fact load
- Data quality checks sau ETL
- OLAP queries + dashboard image outputs

Va de ngo khong gian mo rong cho:

- SCD Type 2
- Partitioning
- BI semantic layer day du hon (SSAS-like)
