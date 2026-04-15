# Do An DW - Submission Checklist

Checklist nay duoc tao theo `Project.pdf` va doi chieu voi source hien tai trong repo.

## 1) Ho so can nop len Google Drive

- [ ] Bao cao (mau do an)
- [ ] Slide trinh bay
- [ ] De tai (link nhom Zalo)
- [ ] readMe.txt
- [ ] Video demo

## 2) Noi dung bat buoc trong bao cao (theo de bai)

- [x] Import du lieu Excel
  - Trang thai hien tai: ETL da doc `.xlsx` trong `etl/python_etl/extract.py`.
- [x] Thiet ke logical
  - Trang thai hien tai: co schema trong `Schema/create_tables.sql`.
  - [ ] Can bo sung hinh/phan mo ta logical model trong bao cao (fact, dimensions, grain, keys).
- [x] Khai thac du lieu (Query, Report, Phan tich)
  - Trang thai hien tai: co bo truy van trong `analysis/query_olap.sql`.
  - Trang thai hien tai: da co script xuat dashboard/report va anh output trong `analysis/dashboard_report.py` -> `analysis/output/`.
  - [ ] Can dua anh output vao bao cao/slide.
- [x] Thiet ke physical
  - Trang thai hien tai: co index trong `Schema/create_index.sql`, co materialized view trong `analysis/query_olap.sql`.
  - [ ] Can viet ro chien luoc refresh MV va ly do chon index.
- [x] SSIS, ETL hoac tuong duong (Pentaho,...)
  - Trang thai hien tai: ETL bang Python (tuong duong) trong `etl/python_etl/`.
- [ ] SSAS, SSRS hoac tuong duong (Pentaho,...)
  - Trang thai hien tai: da bo sung dashboard/report script (tuong duong muc report co ban) trong `analysis/dashboard_report.py`.
  - [ ] Neu can diem cao hon, bo sung them dashboard tren cong cu BI GUI (Power BI/Metabase/Tableau/Pentaho).

## 3) Cac hang muc ky thuat da co trong repo

- [x] Pipeline chay end-to-end: `run.sh`, `run.py`
- [x] ETL tách module: `extract.py`, `clean.py`, `load.py`, `main.py`
- [x] Staging table: `stg_jobs_clean` trong `etl/python_etl/load.py`
- [x] Fact + dimensions + bridge table cho skill
- [x] Truy van OLAP co slice/dice/drilldown/top-N

## 4) Cac hang muc can bo sung de "sat slide" hon

- [ ] Viet ro grain cua fact table trong bao cao/README
  - Goi y: "1 fact row = 1 job posting theo posting_date + context dimensions".
- [ ] Mo ta hierarchy dimensions (dac biet time/location/job)
- [ ] Neu khong lam SCD Type 2, can ghi ro scope va limitation
- [ ] Bo sung phan BI/report (thay the SSAS/SSRS)
- [ ] Chuan bi test data quality sau ETL (row count, null check, FK check)
  - Trang thai hien tai: da bo sung `analysis/data_quality_checks.sql`.

## 5) readMe.txt can nop (ngoai README.md trong repo)

Theo de bai, file readMe.txt nen co:

- [ ] Ten cong cu su dung + version
  - Goi y hien tai: PostgreSQL, Python, pandas, psycopg2-binary, openpyxl.
- [ ] Link download cong cu/chuong trinh can thiet
- [ ] Cach chay nhanh he thong
- [ ] Cau hinh moi truong (DB_NAME, DB_USER, DB_HOST, DB_PORT)

## 6) Slide trinh bay

- [ ] Bao cao bang tieng Anh (theo yeu cau trong de)
- [ ] Co workflow: Source -> ETL -> DW schema -> Query/BI output
- [ ] Co 2-3 phan tich nghiep vu chinh tu dataset

## 7) Truoc khi nop (deadline hygiene)

- [ ] Dong bo ten file, folder, link Drive
- [ ] Test chay lai tu dau bang `./run.sh`
- [ ] Chup man hinh ket qua truy van/report
- [ ] Kiem tra video mo duoc, khong loi font/encoding
- [ ] Gui link Drive cho GV truoc han theo yeu cau
