-- =========================
-- 1. DIMENSION TABLES
-- =========================

DROP TABLE IF EXISTS bridge_job_skill CASCADE;
DROP TABLE IF EXISTS fact_job CASCADE;
DROP TABLE IF EXISTS dim_preference CASCADE;
DROP TABLE IF EXISTS dim_portal CASCADE;
DROP TABLE IF EXISTS dim_skill CASCADE;
DROP TABLE IF EXISTS dim_job CASCADE;
DROP TABLE IF EXISTS dim_company CASCADE;
DROP TABLE IF EXISTS dim_location CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;

CREATE TABLE dim_time (
    time_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL
);

CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    UNIQUE (city, country, latitude, longitude)
);

CREATE TABLE dim_company (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT NOT NULL,
    company_size TEXT,
    sector TEXT,
    industry TEXT,
    city TEXT,
    state TEXT,
    UNIQUE (company_name)
);

CREATE TABLE dim_job (
    job_dim_id SERIAL PRIMARY KEY,
    job_title TEXT NOT NULL,
    role TEXT,
    work_type TEXT,
    qualification TEXT,
    UNIQUE (job_title, role, work_type, qualification)
);

CREATE TABLE dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_name TEXT UNIQUE
);

CREATE TABLE dim_portal (
    portal_id SERIAL PRIMARY KEY,
    portal_name TEXT UNIQUE NOT NULL
);

CREATE TABLE dim_preference (
    preference_id SERIAL PRIMARY KEY,
    preference_name TEXT UNIQUE NOT NULL
);

-- =========================
-- 2. FACT TABLE
-- =========================

CREATE TABLE fact_job (
    fact_job_id BIGSERIAL PRIMARY KEY,
    job_id BIGINT UNIQUE,
    time_id INT NOT NULL,
    location_id INT NOT NULL,
    company_id INT NOT NULL,
    job_dim_id INT NOT NULL,
    portal_id INT NOT NULL,
    preference_id INT NOT NULL,
    min_salary NUMERIC,
    max_salary NUMERIC,
    min_experience_years INT,
    max_experience_years INT,
    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (company_id) REFERENCES dim_company(company_id),
    FOREIGN KEY (job_dim_id) REFERENCES dim_job(job_dim_id),
    FOREIGN KEY (portal_id) REFERENCES dim_portal(portal_id),
    FOREIGN KEY (preference_id) REFERENCES dim_preference(preference_id)
);

-- =========================
-- 3. BRIDGE TABLE
-- =========================

CREATE TABLE bridge_job_skill (
    fact_job_id BIGINT,
    skill_id INT,

    PRIMARY KEY (fact_job_id, skill_id),

    FOREIGN KEY (fact_job_id) REFERENCES fact_job(fact_job_id),
    FOREIGN KEY (skill_id) REFERENCES dim_skill(skill_id)
);

