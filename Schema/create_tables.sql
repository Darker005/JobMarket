-- =========================================
-- 0. RESET (idempotent pipeline)
-- =========================================
DROP TABLE IF EXISTS bridge_job_skill CASCADE;
DROP TABLE IF EXISTS bridge_job_benefit CASCADE;
DROP TABLE IF EXISTS fact_job_posting CASCADE;
DROP TABLE IF EXISTS dim_benefit CASCADE;
DROP TABLE IF EXISTS dim_skill CASCADE;
DROP TABLE IF EXISTS dim_portal CASCADE;
DROP TABLE IF EXISTS dim_preference CASCADE;
DROP TABLE IF EXISTS dim_work_type CASCADE;
DROP TABLE IF EXISTS dim_qualification CASCADE;
DROP TABLE IF EXISTS dim_experience CASCADE;
DROP TABLE IF EXISTS dim_job CASCADE;
DROP TABLE IF EXISTS dim_company CASCADE;
DROP TABLE IF EXISTS dim_location CASCADE;
DROP TABLE IF EXISTS dim_time CASCADE;

-- =========================================
-- 1. DIMENSION TABLES
-- =========================================

-- =========================================
-- DIM TIME
-- =========================================
CREATE TABLE dim_time (

    time_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    full_date DATE UNIQUE NOT NULL,

    day INT NOT NULL
        CHECK (day BETWEEN 1 AND 31),

    month INT NOT NULL
        CHECK (month BETWEEN 1 AND 12),

    quarter INT NOT NULL
        CHECK (quarter BETWEEN 1 AND 4),

    year INT NOT NULL
        CHECK (year >= 2000)
);

-- =========================================
-- DIM LOCATION
-- =========================================
CREATE TABLE dim_location (

    location_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    country TEXT NOT NULL,

    city TEXT NOT NULL,

    latitude DOUBLE PRECISION
        CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),

    longitude DOUBLE PRECISION
        CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),

    UNIQUE (country, city)
);

-- =========================================
-- DIM COMPANY
-- =========================================
CREATE TABLE dim_company (

    company_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    company_name TEXT UNIQUE NOT NULL,

    company_size TEXT,

    industry TEXT,

    sector TEXT,

    website TEXT,

    ticker TEXT
);

-- =========================================
-- DIM JOB
-- =========================================
CREATE TABLE dim_job (

    job_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    job_title TEXT NOT NULL,

    role TEXT,

    UNIQUE (job_title, role)
);

-- =========================================
-- DIM EXPERIENCE
-- =========================================
CREATE TABLE dim_experience (

    experience_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    experience_text TEXT UNIQUE NOT NULL,

    min_years INT
        CHECK (min_years IS NULL OR min_years >= 0),

    max_years INT
        CHECK (max_years IS NULL OR min_years IS NULL OR max_years >= min_years),

    experience_band TEXT
);

-- =========================================
-- DIM QUALIFICATION
-- =========================================
CREATE TABLE dim_qualification (

    qualification_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    qualification_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- DIM WORK TYPE
-- =========================================
CREATE TABLE dim_work_type (

    work_type_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    work_type_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- DIM PREFERENCE
-- =========================================
CREATE TABLE dim_preference (

    preference_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    preference_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- DIM PORTAL
-- =========================================
CREATE TABLE dim_portal (

    portal_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    portal_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- DIM SKILL
-- =========================================
CREATE TABLE dim_skill (

    skill_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    skill_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- DIM BENEFIT
-- =========================================
CREATE TABLE dim_benefit (

    benefit_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    benefit_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- 2. FACT TABLE
-- =========================================
CREATE TABLE fact_job_posting (

    fact_job_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- Business Key
    source_job_id BIGINT UNIQUE NOT NULL,

    -- Foreign Keys
    time_id INT NOT NULL,
    location_id INT NOT NULL,
    company_id INT NOT NULL,
    job_id INT NOT NULL,
    experience_id INT NOT NULL,
    qualification_id INT NOT NULL,
    work_type_id INT NOT NULL,
    preference_id INT NOT NULL,
    portal_id INT NOT NULL,

    -- Measures
    min_salary NUMERIC(12,2)
        CHECK (min_salary IS NULL OR min_salary >= 0),

    max_salary NUMERIC(12,2)
        CHECK (max_salary IS NULL OR min_salary IS NULL OR max_salary >= min_salary),

    skill_count INT DEFAULT 0
        CHECK (skill_count >= 0),

    benefit_count INT DEFAULT 0
        CHECK (benefit_count >= 0),

    job_count INT DEFAULT 1
        CHECK (job_count >= 1),

    -- Foreign Keys Constraints
    CONSTRAINT fk_time
        FOREIGN KEY (time_id)
        REFERENCES dim_time(time_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_location
        FOREIGN KEY (location_id)
        REFERENCES dim_location(location_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_company
        FOREIGN KEY (company_id)
        REFERENCES dim_company(company_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_job
        FOREIGN KEY (job_id)
        REFERENCES dim_job(job_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_experience
        FOREIGN KEY (experience_id)
        REFERENCES dim_experience(experience_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_qualification
        FOREIGN KEY (qualification_id)
        REFERENCES dim_qualification(qualification_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_work_type
        FOREIGN KEY (work_type_id)
        REFERENCES dim_work_type(work_type_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_preference
        FOREIGN KEY (preference_id)
        REFERENCES dim_preference(preference_id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_portal
        FOREIGN KEY (portal_id)
        REFERENCES dim_portal(portal_id)
        ON DELETE RESTRICT
);

-- =========================================
-- 3. BRIDGE TABLES
-- =========================================

-- =========================================
-- BRIDGE JOB SKILL
-- =========================================
CREATE TABLE bridge_job_skill (

    fact_job_id BIGINT NOT NULL,

    skill_id INT NOT NULL,

    PRIMARY KEY (fact_job_id, skill_id),

    CONSTRAINT fk_fact_job_skill
        FOREIGN KEY (fact_job_id)
        REFERENCES fact_job_posting(fact_job_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_skill
        FOREIGN KEY (skill_id)
        REFERENCES dim_skill(skill_id)
        ON DELETE RESTRICT
);

-- =========================================
-- BRIDGE JOB BENEFIT
-- =========================================
CREATE TABLE bridge_job_benefit (

    fact_job_id BIGINT NOT NULL,

    benefit_id INT NOT NULL,

    PRIMARY KEY (fact_job_id, benefit_id),

    CONSTRAINT fk_fact_job_benefit
        FOREIGN KEY (fact_job_id)
        REFERENCES fact_job_posting(fact_job_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_benefit
        FOREIGN KEY (benefit_id)
        REFERENCES dim_benefit(benefit_id)
        ON DELETE RESTRICT
);

-- 
-- NHỮNG BUSINESS QUESTIONS MÀ BẢN MODEL NÀY CÓ THỂ TRẢ LỜI ĐƯỢC
-- (xem file gốc team; metric lương trung bình dùng (min_salary+max_salary)/2 trên fact)
-- 
