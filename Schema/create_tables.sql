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
        CHECK (latitude BETWEEN -90 AND 90),

    longitude DOUBLE PRECISION
        CHECK (longitude BETWEEN -180 AND 180),

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
        CHECK (min_years >= 0),

    max_years INT
        CHECK (max_years >= min_years),

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
        CHECK (min_salary >= 0),

    max_salary NUMERIC(12,2)
        CHECK (max_salary >= min_salary),

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
-- NHŨNG BUSINESS QUESTIONS MÀ BẢN MODEL NÀY CÓ THỂ TRẢ LỜI ĐƯỢC
-- 

-- 💰 I. SALARY ANALYTICS
-- ✅ BQ1 — Country nào lương cao nhất?
-- Tables
-- fact_job_posting
-- dim_location
-- Measures
-- AVG(avg_salary)
-- ✅ BQ2 — Industry nào lương cao nhất?
-- Tables
-- fact_job_posting
-- dim_company
-- Measures
-- AVG(avg_salary)
-- ✅ BQ3 — Work type nào lương cao nhất?
-- Tables
-- fact_job_posting
-- dim_work_type
-- ✅ BQ4 — Qualification vs salary
-- Tables
-- fact_job_posting
-- dim_qualification
-- ✅ BQ5 — Experience ảnh hưởng salary
-- Tables
-- fact_job_posting
-- dim_experience
-- Measures
-- AVG(avg_salary)
-- ✅ BQ6 — Top job roles salary cao nhất
-- Tables
-- fact_job_posting
-- dim_job
-- ✅ BQ7 — Company size vs salary
-- Tables
-- fact_job_posting
-- dim_company
-- ✅ BQ8 — Preference vs salary
-- Tables
-- fact_job_posting
-- dim_preference
-- 🧠 II. SKILL ANALYTICS
-- ✅ BQ9 — Skill nào phổ biến nhất?
-- Tables
-- bridge_job_skill
-- dim_skill
-- Measures
-- COUNT(*)
-- ✅ BQ10 — Skill nào salary cao nhất?
-- Tables
-- bridge_job_skill
-- dim_skill
-- fact_job_posting
-- ✅ BQ11 — Skill combinations phổ biến nhất
-- Logic
-- self join bridge table
-- ✅ BQ12 — Industry cần nhiều skill nhất
-- Tables
-- dim_company
-- bridge_job_skill
-- ✅ BQ13 — Top skills theo industry
-- Tables
-- dim_company
-- bridge_job_skill
-- dim_skill
-- ✅ BQ14 — Skill demand theo thời gian
-- Tables
-- dim_time
-- bridge_job_skill
-- dim_skill
-- 🌍 III. GEOGRAPHIC ANALYTICS
-- ✅ BQ15 — Country nào có nhiều jobs nhất
-- Tables
-- fact_job_posting
-- dim_location
-- ✅ BQ16 — Location salary cao nhất
-- Tables
-- fact_job_posting
-- dim_location
-- ✅ BQ17 — Hiring trend theo thời gian + country
-- Tables
-- fact_job_posting
-- dim_time
-- dim_location
-- ✅ BQ18 — Work type distribution theo location
-- Tables
-- fact_job_posting
-- dim_location
-- dim_work_type
-- ✅ BQ19 — Remote jobs tập trung ở đâu
-- Tables
-- dim_work_type
-- dim_location
-- 🏢 IV. COMPANY & INDUSTRY ANALYTICS
-- ✅ BQ20 — Industry có hiring demand cao nhất
-- Tables
-- fact_job_posting
-- dim_company
-- ✅ BQ21 — Sector hiring trend theo thời gian
-- Tables
-- fact_job_posting
-- dim_company
-- dim_time
-- ✅ BQ22 — Top companies tuyển dụng nhiều nhất
-- Tables
-- fact_job_posting
-- dim_company
-- ✅ BQ23 — Portal nào có nhiều jobs nhất
-- Tables
-- fact_job_posting
-- dim_portal
-- ✅ BQ24 — Portal specialization theo role
-- Tables
-- fact_job_posting
-- dim_portal
-- dim_job
-- ✅ BQ25 — Industry hiring diversity
-- Tables
-- fact_job_posting
-- dim_company
-- dim_job
-- 📈 V. TREND ANALYTICS
-- ✅ BQ26 — Job postings theo năm
-- Tables
-- fact_job_posting
-- dim_time
-- ✅ BQ27 — Salary trend theo thời gian
-- Tables
-- fact_job_posting
-- dim_time
-- ✅ BQ28 — Skill demand trend
-- Tables
-- bridge_job_skill
-- dim_time
-- dim_skill
-- ✅ BQ29 — Industry hiring trend theo thời gian
-- Tables
-- fact_job_posting
-- dim_company
-- dim_time
-- ✅ BQ30 — Top growing industries
-- Tables
-- fact_job_posting
-- dim_company
-- dim_time
-- ✅ BQ31 — Top growing skills
-- Tables
-- bridge_job_skill
-- dim_skill
-- dim_time
-- 🎁 VI. BENEFIT ANALYTICS
-- ✅ BQ32 — Benefit nào phổ biến nhất
-- Tables
-- bridge_job_benefit
-- dim_benefit
-- ✅ BQ33 — Benefit nào liên quan salary cao
-- Tables
-- bridge_job_benefit
-- dim_benefit
-- fact_job_posting
-- ✅ BQ34 — Industry nào cung cấp nhiều benefits nhất
-- Tables
-- bridge_job_benefit
-- dim_company
-- ✅ BQ35 — Company size vs benefits
-- Tables
-- bridge_job_benefit
-- dim_company
-- 👥 VII. HR ANALYTICS
-- ✅ BQ36 — Female/Male preference theo role
-- Tables
-- dim_preference
-- dim_job
-- fact_job_posting
-- ✅ BQ37 — Qualification phổ biến theo industry
-- Tables
-- dim_company
-- dim_qualification
-- fact_job_posting
-- ✅ BQ38 — Experience level demand
-- Tables
-- dim_experience
-- fact_job_posting
-- ✅ BQ39 — Experience vs work type
-- Tables
-- dim_experience
-- dim_work_type
-- fact_job_posting
-- 🤖 VIII. BASIC PREDICTIVE ANALYTICS
-- ✅ BQ40 — Predict salary
-- Features available
-- experience
-- qualification
-- role
-- work type
-- country
-- industry
-- skills
-- ✅ BQ41 — Predict hot skills
-- Tables
-- bridge_job_skill
-- dim_skill
-- dim_time
-- 🔥 IX. ADVANCED / WOW FACTOR
-- ✅ BQ42 — Job similarity engine
-- Based on
-- skills
-- salary
-- role
-- ✅ BQ43 — Recruitment recommendation system
-- Inputs
-- salary budget
-- role
-- skills
-- Outputs
-- best countries
-- best industries
