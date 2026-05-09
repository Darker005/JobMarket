# JobMarket Requirement Mapping

## 1) Raw Input to Warehouse Mapping

| Raw Column | Warehouse Target | Notes |
|---|---|---|
| Job Id | fact_job.job_id | Natural business key for dedup/upsert |
| Experience | fact_job.min_experience_years, fact_job.max_experience_years | Parse from text range ("5 to 15 Years") |
| Qualifications | dim_job.qualification | Normalized text |
| Salary Range | derived only | Keep for reference, use Min/Max Salary as source of truth |
| Min Salary | fact_job.min_salary | Numeric |
| Max Salary | fact_job.max_salary | Numeric |
| location | dim_location.city | City name |
| Country | dim_location.country | Country name |
| latitude | dim_location.latitude | Numeric float |
| longitude | dim_location.longitude | Numeric float |
| Work Type | dim_job.work_type | Full-Time/Part-Time/Contract/Intern/... |
| Company Size | dim_company.company_size | Organization size bucket |
| Job Posting Date | dim_time.full_date | Supports Excel serial and date-like strings |
| Preference | dim_preference.preference_name | Candidate preference segment |
| Contact Person | optional (not modeled) | Can be added later if contact analytics required |
| Contact | optional (not modeled) | Can be added later if contact analytics required |
| Job Title | dim_job.job_title | Job title |
| Role | dim_job.role | Role family |
| Job Portal | dim_portal.portal_name | Source channel |
| Job Description | optional (not modeled) | Candidate for NLP phase |
| Benefits | dim_benefit + bridge_job_benefit | Tokenized list |
| skills | dim_skill + bridge_job_skill | Tokenized list |
| Responsibilities | optional (not modeled) | Candidate for NLP phase |
| Company | dim_company.company_name | Company name |
| Company Profile | dim_company.sector/industry/city/state/zip/website/ticker/ceo | JSON payload |

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

- Grain of fact: one job posting per `job_id`.
- Salary metric for analytics:
  - `avg_salary = (min_salary + max_salary) / 2`
- Skill and benefit are many-to-many attributes:
  - `bridge_job_skill`, `bridge_job_benefit`
- Time dimension sourced from posting date.

## 4) Current Constraints

- Contact/description/responsibility fields are not yet in dimensional model.
- Advanced recommendation and deep NLP are deferred to Phase D.
