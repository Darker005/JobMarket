-- =========================
-- 1. DIMENSION TABLES
-- =========================

CREATE TABLE dim_time (
    time_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE,
    day INT,
    month INT,
    year INT,
    quarter INT
);

CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    city VARCHAR(100),
    country VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE dim_company (
    company_id SERIAL PRIMARY KEY,
    company_name VARCHAR(255),
    company_size VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100)
);

CREATE TABLE dim_job (
    job_dim_id SERIAL PRIMARY KEY,
    job_title VARCHAR(255),
    role VARCHAR(100),
    work_type VARCHAR(50),
    experience VARCHAR(50),
    qualification VARCHAR(100)
);

CREATE TABLE dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_name VARCHAR(255) UNIQUE
);

-- =========================
-- 2. FACT TABLE
-- =========================

CREATE TABLE fact_job (
    job_id BIGINT PRIMARY KEY,
    time_id INT,
    location_id INT,
    company_id INT,
    job_dim_id INT,

    min_salary NUMERIC,
    max_salary NUMERIC,

    FOREIGN KEY (time_id) REFERENCES dim_time(time_id),
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (company_id) REFERENCES dim_company(company_id),
    FOREIGN KEY (job_dim_id) REFERENCES dim_job(job_dim_id)
);

-- =========================
-- 3. BRIDGE TABLE
-- =========================

CREATE TABLE bridge_job_skill (
    job_id BIGINT,
    skill_id INT,

    PRIMARY KEY (job_id, skill_id),

    FOREIGN KEY (job_id) REFERENCES fact_job(job_id),
    FOREIGN KEY (skill_id) REFERENCES dim_skill(skill_id)
);

