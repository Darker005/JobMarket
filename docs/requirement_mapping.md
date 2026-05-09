# JobMarket Requirement Mapping

## 1) Raw Input to Warehouse Mapping

| Raw Column | Warehouse Target | Notes |
|---|---|---|
| Job Id | fact_job_posting.source_job_id | Khóa nghiệp vụ, UNIQUE |
| Experience | dim_experience (+ min/max years parse) | Text gốc → experience_text; năm parse vào min_years/max_years |
| Qualifications | dim_qualification.qualification_name | |
| Salary Range | derived only | Chỉ min/max salary là nguồn số |
| Min Salary | fact_job_posting.min_salary | NUMERIC(12,2) |
| Max Salary | fact_job_posting.max_salary | NUMERIC(12,2) |
| location | dim_location.city | UNIQUE cùng country |
| Country | dim_location.country | |
| latitude / longitude | dim_location | CHECK tọa độ; cùng (country,city) một dòng location |
| Work Type | dim_work_type.work_type_name | |
| Company Size | dim_company.company_size | |
| Job Posting Date | dim_time.full_date | Excel serial / chuỗi ngày |
| Preference | dim_preference.preference_name | |
| Contact Person / Contact | *(chưa model)* | |
| Job Title | dim_job.job_title | dim_job chỉ (title, role) |
| Role | dim_job.role | |
| Job Portal | dim_portal.portal_name | |
| Job Description / Responsibilities | *(chưa model)* | |
| Benefits | dim_benefit + bridge_job_benefit; fact_job_posting.benefit_count | |
| skills | dim_skill + bridge_job_skill; fact_job_posting.skill_count | |
| Company | dim_company.company_name | |
| Company Profile | dim_company sector/industry/website/ticker | JSON parse; city/state/zip/ceo chỉ còn trên staging ETL nếu cần sau |

## 2) Delivery Scope by Phase

### Phase A (MVP): Salary + Geo + Company + Trend Baseline

- BQ1-5: salary by country/city/industry/sector/work type
- BQ21-24: geographic demand + hiring trend by country
- BQ29-32: industry demand/top companies/top portal
- BQ36-38: posting and salary trend by time

### Phase B: Skill + Benefit + Cross Dimension

- BQ11-18: top skills, salary by skill, rarity/variance, demand trend
- BQ52-55: benefits popularity, salary linkage, industry/company-size effects

### Phase C: Trend Advanced + HR + Cost

- BQ39-59: velocity, volatility, HR slices, cost-effectiveness signals

### Phase D: Predictive / Advanced

- BQ60-66: predictive salary, hot skill forecast, hiring trend forecast, recommendation prototype

## 3) Modeling Decisions

- Grain: một dòng `fact_job_posting` = một tin tuyển dụng theo `source_job_id`.
- Salary metric: `avg_salary = (min_salary + max_salary) / 2` (không cột avg trên fact).
- Skill / benefit: bridge + `skill_count` / `benefit_count` trên fact.
- Experience / qualification / work type: dimension riêng (chuẩn hoá theo schema team).

## 4) Current Constraints

- Contact/description/responsibility fields are not yet in dimensional model.
- Advanced recommendation and deep NLP are deferred to Phase D.
