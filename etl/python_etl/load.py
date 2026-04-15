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

INSERT INTO dim_location (city, country, latitude, longitude)
SELECT DISTINCT city, country, latitude, longitude
FROM stg_jobs_clean
ON CONFLICT (city, country, latitude, longitude) DO NOTHING;

INSERT INTO dim_company (company_name, company_size, sector, industry, city, state)
SELECT DISTINCT company_name, company_size, sector, industry, company_city, company_state
FROM stg_jobs_clean
ON CONFLICT (company_name) DO NOTHING;

INSERT INTO dim_job (job_title, role, work_type, qualification)
SELECT DISTINCT job_title, role, work_type, qualification
FROM stg_jobs_clean
ON CONFLICT (job_title, role, work_type, qualification) DO NOTHING;

INSERT INTO dim_portal (portal_name)
SELECT DISTINCT portal_name FROM stg_jobs_clean
ON CONFLICT (portal_name) DO NOTHING;

INSERT INTO dim_preference (preference_name)
SELECT DISTINCT preference_name FROM stg_jobs_clean
ON CONFLICT (preference_name) DO NOTHING;

INSERT INTO fact_job (
    job_id, time_id, location_id, company_id, job_dim_id, portal_id, preference_id,
    min_salary, max_salary, min_experience_years, max_experience_years
)
SELECT
    s.job_id,
    t.time_id,
    l.location_id,
    c.company_id,
    j.job_dim_id,
    p.portal_id,
    pr.preference_id,
    s.min_salary,
    s.max_salary,
    s.min_experience_years,
    s.max_experience_years
FROM stg_jobs_clean s
JOIN dim_time t ON t.full_date = s.posting_date
JOIN dim_location l
  ON l.city = s.city
 AND l.country = s.country
 AND COALESCE(l.latitude, 0) = COALESCE(s.latitude, 0)
 AND COALESCE(l.longitude, 0) = COALESCE(s.longitude, 0)
JOIN dim_company c ON c.company_name = s.company_name
JOIN dim_job j
  ON j.job_title = s.job_title
 AND COALESCE(j.role, '') = COALESCE(s.role, '')
 AND COALESCE(j.work_type, '') = COALESCE(s.work_type, '')
 AND COALESCE(j.qualification, '') = COALESCE(s.qualification, '')
JOIN dim_portal p ON p.portal_name = s.portal_name
JOIN dim_preference pr ON pr.preference_name = s.preference_name
ON CONFLICT (job_id) DO NOTHING;

WITH exploded AS (
  SELECT
    f.fact_job_id,
    TRIM(skill_token) AS skill_name
  FROM stg_jobs_clean s
  JOIN fact_job f ON f.job_id = s.job_id
  CROSS JOIN LATERAL regexp_split_to_table(
    regexp_replace(COALESCE(s.skills_raw, ''), '[{}]', '', 'g'),
    ','
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
  JOIN fact_job f ON f.job_id = s.job_id
  CROSS JOIN LATERAL regexp_split_to_table(
    regexp_replace(COALESCE(s.skills_raw, ''), '[{}]', '', 'g'),
    ','
  ) AS skill_token
)
INSERT INTO bridge_job_skill (fact_job_id, skill_id)
SELECT DISTINCT e.fact_job_id, ds.skill_id
FROM exploded e
JOIN dim_skill ds ON ds.skill_name = e.skill_name
WHERE e.skill_name <> ''
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
    "min_salary",
    "max_salary",
    "min_experience_years",
    "max_experience_years",
    "skills_raw",
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
                min_salary NUMERIC,
                max_salary NUMERIC,
                min_experience_years INT,
                max_experience_years INT,
                skills_raw TEXT
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
                industry, company_city, company_state, min_salary, max_salary, min_experience_years,
                max_experience_years, skills_raw
            ) FROM STDIN WITH (FORMAT csv, NULL '')
            """,
            out,
        )
    conn.commit()


def upsert_dw(conn):
    with conn.cursor() as cur:
        cur.execute(UPSERT_SQL)
    conn.commit()

