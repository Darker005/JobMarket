import io

import psycopg2


UPSERT_SQL = """
INSERT INTO dim_time (full_date, day, month, year, quarter)
SELECT DISTINCT
    posting_date,
    EXTRACT(DAY FROM posting_date)::INT,
    EXTRACT(MONTH FROM posting_date)::INT,
    EXTRACT(YEAR FROM posting_date)::INT,
    EXTRACT(QUARTER FROM posting_date)::INT
FROM stg_jobs_clean
ON CONFLICT (full_date) DO NOTHING;

INSERT INTO dim_location (country, city, latitude, longitude)
SELECT DISTINCT ON (country, city)
    country, city, latitude, longitude
FROM stg_jobs_clean
ORDER BY country, city, latitude NULLS LAST
ON CONFLICT (country, city) DO NOTHING;

INSERT INTO dim_company (company_name, company_size, industry, sector, website, ticker)
SELECT DISTINCT
    company_name, company_size, industry, sector, company_website, company_ticker
FROM stg_jobs_clean
ON CONFLICT (company_name) DO NOTHING;

INSERT INTO dim_job (job_title, role)
SELECT DISTINCT job_title, role
FROM stg_jobs_clean
ON CONFLICT (job_title, role) DO NOTHING;

INSERT INTO dim_experience (experience_text, min_years, max_years, experience_band)
SELECT DISTINCT experience_text, min_experience_years, max_experience_years, NULL
FROM stg_jobs_clean
ON CONFLICT (experience_text) DO NOTHING;

INSERT INTO dim_qualification (qualification_name)
SELECT DISTINCT qualification
FROM stg_jobs_clean
ON CONFLICT (qualification_name) DO NOTHING;

INSERT INTO dim_work_type (work_type_name)
SELECT DISTINCT work_type
FROM stg_jobs_clean
ON CONFLICT (work_type_name) DO NOTHING;

INSERT INTO dim_portal (portal_name)
SELECT DISTINCT portal_name FROM stg_jobs_clean
ON CONFLICT (portal_name) DO NOTHING;

INSERT INTO dim_preference (preference_name)
SELECT DISTINCT preference_name FROM stg_jobs_clean
ON CONFLICT (preference_name) DO NOTHING;

INSERT INTO fact_job_posting (
    source_job_id, time_id, location_id, company_id, job_id,
    experience_id, qualification_id, work_type_id, preference_id, portal_id,
    min_salary, max_salary, skill_count, benefit_count, job_count
)
SELECT
    s.job_id,
    t.time_id,
    l.location_id,
    c.company_id,
    j.job_id,
    e.experience_id,
    q.qualification_id,
    w.work_type_id,
    pr.preference_id,
    p.portal_id,
    s.min_salary,
    s.max_salary,
    s.skill_count,
    s.benefit_count,
    1
FROM stg_jobs_clean s
JOIN dim_time t ON t.full_date = s.posting_date
JOIN dim_location l ON l.country = s.country AND l.city = s.city
JOIN dim_company c ON c.company_name = s.company_name
JOIN dim_job j ON j.job_title = s.job_title AND COALESCE(j.role, '') = COALESCE(s.role, '')
JOIN dim_experience e ON e.experience_text = s.experience_text
JOIN dim_qualification q ON q.qualification_name = s.qualification
JOIN dim_work_type w ON w.work_type_name = s.work_type
JOIN dim_portal p ON p.portal_name = s.portal_name
JOIN dim_preference pr ON pr.preference_name = s.preference_name
ON CONFLICT (source_job_id) DO NOTHING;

WITH exploded AS (
  SELECT
    f.fact_job_id,
    TRIM(skill_token) AS skill_name
  FROM stg_jobs_clean s
  JOIN fact_job_posting f ON f.source_job_id = s.job_id
  CROSS JOIN LATERAL regexp_split_to_table(
    COALESCE(s.skills_raw, ''),
    '\\|'
  ) AS skill_token
)
INSERT INTO dim_skill (skill_name)
SELECT DISTINCT skill_name
FROM exploded
WHERE skill_name <> ''
ON CONFLICT (skill_name) DO NOTHING;

WITH exploded AS (
  SELECT
    f.fact_job_id,
    TRIM(skill_token) AS skill_name
  FROM stg_jobs_clean s
  JOIN fact_job_posting f ON f.source_job_id = s.job_id
  CROSS JOIN LATERAL regexp_split_to_table(
    COALESCE(s.skills_raw, ''),
    '\\|'
  ) AS skill_token
)
INSERT INTO bridge_job_skill (fact_job_id, skill_id)
SELECT DISTINCT e.fact_job_id, ds.skill_id
FROM exploded e
JOIN dim_skill ds ON ds.skill_name = e.skill_name
WHERE e.skill_name <> ''
ON CONFLICT DO NOTHING;

WITH exploded AS (
  SELECT
    f.fact_job_id,
    TRIM(benefit_token) AS benefit_name
  FROM stg_jobs_clean s
  JOIN fact_job_posting f ON f.source_job_id = s.job_id
  CROSS JOIN LATERAL regexp_split_to_table(
    COALESCE(s.benefits_raw, ''),
    '\\|'
  ) AS benefit_token
)
INSERT INTO dim_benefit (benefit_name)
SELECT DISTINCT benefit_name
FROM exploded
WHERE benefit_name <> ''
ON CONFLICT (benefit_name) DO NOTHING;

WITH exploded AS (
  SELECT
    f.fact_job_id,
    TRIM(benefit_token) AS benefit_name
  FROM stg_jobs_clean s
  JOIN fact_job_posting f ON f.source_job_id = s.job_id
  CROSS JOIN LATERAL regexp_split_to_table(
    COALESCE(s.benefits_raw, ''),
    '\\|'
  ) AS benefit_token
)
INSERT INTO bridge_job_benefit (fact_job_id, benefit_id)
SELECT DISTINCT e.fact_job_id, db.benefit_id
FROM exploded e
JOIN dim_benefit db ON db.benefit_name = e.benefit_name
WHERE e.benefit_name <> ''
ON CONFLICT DO NOTHING;
"""


EXPORT_COLUMNS = [
    "job_id",
    "posting_date",
    "city",
    "country",
    "latitude",
    "longitude",
    "work_type",
    "qualification",
    "preference_name",
    "job_title",
    "role",
    "portal_name",
    "company_name",
    "company_size",
    "sector",
    "industry",
    "company_city",
    "company_state",
    "company_zip",
    "company_website",
    "company_ticker",
    "company_ceo",
    "min_salary",
    "max_salary",
    "min_experience_years",
    "max_experience_years",
    "experience_text",
    "skill_count",
    "benefit_count",
    "skills_raw",
    "benefits_raw",
]


def get_connection(args):
    return psycopg2.connect(
        dbname=args.db_name,
        user=args.db_user,
        host=args.db_host,
        port=args.db_port,
        password=args.db_password,
    )


def load_clean_staging(conn, df):
    with conn.cursor() as cur:
        cur.execute(
            """
            DROP TABLE IF EXISTS stg_jobs_clean;
            CREATE TABLE stg_jobs_clean (
                job_id BIGINT,
                posting_date DATE,
                city TEXT,
                country TEXT,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                work_type TEXT,
                qualification TEXT,
                preference_name TEXT,
                job_title TEXT,
                role TEXT,
                portal_name TEXT,
                company_name TEXT,
                company_size TEXT,
                sector TEXT,
                industry TEXT,
                company_city TEXT,
                company_state TEXT,
                company_zip TEXT,
                company_website TEXT,
                company_ticker TEXT,
                company_ceo TEXT,
                min_salary NUMERIC,
                max_salary NUMERIC,
                min_experience_years INT,
                max_experience_years INT,
                experience_text TEXT,
                skill_count INT,
                benefit_count INT,
                skills_raw TEXT,
                benefits_raw TEXT
            );
            """
        )
        out = io.StringIO()
        df[EXPORT_COLUMNS].to_csv(out, index=False, header=False, na_rep="")
        out.seek(0)
        cur.copy_expert(
            """
            COPY stg_jobs_clean (
                job_id, posting_date, city, country, latitude, longitude, work_type, qualification,
                preference_name, job_title, role, portal_name, company_name, company_size, sector,
                industry, company_city, company_state, company_zip, company_website, company_ticker,
                company_ceo, min_salary, max_salary, min_experience_years, max_experience_years,
                experience_text, skill_count, benefit_count, skills_raw, benefits_raw
            ) FROM STDIN WITH (FORMAT csv, NULL '')
            """,
            out,
        )
    conn.commit()


def upsert_dw(conn):
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL)
    conn.commit()
