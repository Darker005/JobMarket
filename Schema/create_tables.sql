-- =========================================
-- 1. DIMENSION TABLES
-- =========================================

-- =========================
-- DIM TIME
-- =========================
CREATE TABLE dim_time (
    time_id SERIAL PRIMARY KEY,
    full_date DATE UNIQUE NOT NULL,
    day INT NOT NULL CHECK (day BETWEEN 1 AND 31),
    month INT NOT NULL CHECK (month BETWEEN 1 AND 12),
    quarter INT NOT NULL CHECK (quarter BETWEEN 1 AND 4),
    year INT NOT NULL CHECK (year >= 2000)
);

-- =========================
-- DIM LOCATION
-- =========================
CREATE TABLE dim_location (
    location_id SERIAL PRIMARY KEY,
    country TEXT NOT NULL,
    city TEXT NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,

    UNIQUE (country, city)
);

-- =========================
-- DIM COMPANY
-- =========================
CREATE TABLE dim_company (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT UNIQUE NOT NULL,
    company_size TEXT,
    industry TEXT,
    sector TEXT
);

-- =========================
-- DIM JOB
-- =========================
CREATE TABLE dim_job (
    job_id SERIAL PRIMARY KEY,

    job_title TEXT NOT NULL,
    role TEXT,
    work_type TEXT,
    qualification TEXT,
    experience_level TEXT,
    preference TEXT,

    UNIQUE (
        job_title,
        role,
        work_type,
        qualification,
        preference
    )
);

-- =========================
-- DIM PORTAL
-- =========================
CREATE TABLE dim_portal (
    portal_id SERIAL PRIMARY KEY,
    portal_name TEXT UNIQUE NOT NULL
);

-- =========================
-- DIM SKILL
-- =========================
CREATE TABLE dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_name TEXT UNIQUE NOT NULL
);

-- =========================================
-- 2. FACT TABLE
-- =========================================

CREATE TABLE fact_job_posting (

    fact_job_id BIGSERIAL PRIMARY KEY,

    -- Foreign Keys
    time_id INT NOT NULL,
    location_id INT NOT NULL,
    company_id INT NOT NULL,
    job_id INT NOT NULL,
    portal_id INT NOT NULL,

    -- Measures
    min_salary NUMERIC CHECK (min_salary >= 0),
    max_salary NUMERIC CHECK (max_salary >= min_salary),

    min_experience_years INT
        CHECK (min_experience_years >= 0),

    max_experience_years INT
        CHECK (
            max_experience_years >= min_experience_years
        ),

    job_count INT DEFAULT 1 CHECK (job_count >= 1),

    -- Foreign Key Constraints
    CONSTRAINT fk_time
        FOREIGN KEY (time_id)
        REFERENCES dim_time(time_id),

    CONSTRAINT fk_location
        FOREIGN KEY (location_id)
        REFERENCES dim_location(location_id),

    CONSTRAINT fk_company
        FOREIGN KEY (company_id)
        REFERENCES dim_company(company_id),

    CONSTRAINT fk_job
        FOREIGN KEY (job_id)
        REFERENCES dim_job(job_id),

    CONSTRAINT fk_portal
        FOREIGN KEY (portal_id)
        REFERENCES dim_portal(portal_id)
);

-- =========================================
-- 3. BRIDGE TABLE
-- =========================================

CREATE TABLE bridge_job_skill (

    fact_job_id BIGINT NOT NULL,
    skill_id INT NOT NULL,

    PRIMARY KEY (fact_job_id, skill_id),

    CONSTRAINT fk_fact_job
        FOREIGN KEY (fact_job_id)
        REFERENCES fact_job_posting(fact_job_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_skill
        FOREIGN KEY (skill_id)
        REFERENCES dim_skill(skill_id)
        ON DELETE CASCADE
);

-- BQ1 – Country nào lương cao nhất?
-- •	Dim_Location + Fact 
-- •	AVG(salary) 
-- ________________________________________
-- ✔ BQ2 – Industry nào lương cao nhất?
-- •	Dim_Company.industry + Fact 
-- •	AVG(salary) 
-- ________________________________________
-- ✔ BQ3 – Work type nào lương cao nhất?
-- •	Dim_Job.work_type 
-- ________________________________________
-- ✔ BQ4 – Qualification vs salary
-- •	Dim_Job.qualification + Fact 
-- ________________________________________
-- ✔ BQ5 – Experience ảnh hưởng salary
-- •	Fact (experience + salary) 
-- •	GROUP BY experience level 
-- ________________________________________
-- ✔ BQ6 – Top job roles salary cao nhất
-- •	Dim_Job.job_title + Fact 
-- ________________________________________
-- 🧠 II. SKILL ANALYTICS
-- ✔ BQ7 – Skill nào phổ biến nhất?
-- •	Bridge_Job_Skill + Dim_Skill 
-- •	COUNT(skill_id) 
-- ________________________________________
-- ✔ BQ8 – Skill liên quan salary cao?
-- •	Bridge + Fact + Dim_Skill 
-- •	AVG salary per skill 
-- ________________________________________
-- ✔ BQ9 – Skill combinations
-- •	Bridge table self-join 
-- •	hoặc aggregation per job_id 
-- ________________________________________
-- ✔ BQ10 – Industry cần nhiều skill nhất
-- •	Company.industry + Bridge 
-- ________________________________________
-- ✔ BQ11 – Top skills theo industry
-- •	Company + Bridge + Skill 
-- ________________________________________
-- 🌍 III. GEOGRAPHIC ANALYTICS
-- ✔ BQ12 – Country nhiều jobs nhất
-- •	Dim_Location + Fact COUNT 
-- ________________________________________
-- ✔ BQ13 – Location salary cao nhất
-- •	Dim_Location + Fact AVG salary 
-- ________________________________________
-- ✔ BQ14 – Hiring trend theo thời gian + country
-- •	Dim_Time + Dim_Location + Fact 
-- ________________________________________
-- ✔ BQ15 – Work type distribution theo location
-- •	Dim_Location + Dim_Job 
-- ________________________________________
-- 🏢 IV. COMPANY & INDUSTRY
-- ✔ BQ16 – Industry có nhu cầu cao nhất
-- •	Company.industry + Fact COUNT 
-- ________________________________________
-- ✔ BQ17 – Company size vs salary
-- •	Dim_Company.company_size + Fact AVG salary 
-- ________________________________________
-- ✔ BQ18 – Portal nào nhiều jobs nhất
-- •	Dim_Portal + Fact COUNT 
-- ________________________________________
-- ✔ BQ19 – Top companies tuyển dụng nhiều nhất
-- •	Dim_Company + Fact COUNT 
-- ________________________________________
-- ✔ BQ20 – Sector trend theo thời gian
-- •	Dim_Company.sector + Dim_Time + Fact 
-- ________________________________________
-- 📈 V. TREND ANALYTICS
-- ✔ BQ21 – Job postings theo năm
-- •	Dim_Time.year + COUNT(Fact) 
-- ________________________________________
-- ✔ BQ22 – Salary trend theo thời gian
-- •	Dim_Time + AVG salary 
-- ________________________________________
-- ✔ BQ23 – Skill demand theo thời gian
-- •	Bridge + Dim_Time + Skill 
-- ________________________________________
-- ✔ BQ24 – Industry hiring trend theo thời gian
-- •	Company.industry + Dim_Time + Fact
-- ✔ NEW BQ25
-- Job roles nào ưu tiên Female/Male nhiều nhất?
-- ✔ NEW BQ26
-- Salary có khác nhau giữa jobs có preference khác nhau không
