-- =======================================================
-- JobMarket OLAP Query Pack
-- Phase A: MVP (salary/geography/company/time)
-- Phase B/C: skills, benefits, HR, cost analytics
-- =======================================================

-- ---------
-- Phase A
-- ---------
\echo '=== Phase A / BQ1: Country salary ranking ==='
SELECT
    l.country,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.country
ORDER BY avg_salary DESC NULLS LAST, job_count DESC
LIMIT 20;

\echo '=== Phase A / BQ2: City salary ranking ==='
SELECT
    l.country,
    l.city,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.country, l.city
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC NULLS LAST, job_count DESC
LIMIT 20;

\echo '=== Phase A / BQ3-BQ4: Industry/Sector salary ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COALESCE(c.sector, 'Unknown') AS sector,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job f
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.industry, 'Unknown'), COALESCE(c.sector, 'Unknown')
ORDER BY avg_salary DESC NULLS LAST, job_count DESC
LIMIT 25;

\echo '=== Phase A / BQ5: Work type salary ==='
SELECT
    COALESCE(j.work_type, 'Unknown') AS work_type,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job f
JOIN dim_job j ON j.job_dim_id = f.job_dim_id
GROUP BY COALESCE(j.work_type, 'Unknown')
ORDER BY avg_salary DESC NULLS LAST, job_count DESC;

\echo '=== Phase A / BQ21-BQ24-BQ36-BQ38: Monthly trend ==='
SELECT
    t.year,
    t.month,
    l.country,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY t.year, t.month, l.country
ORDER BY t.year, t.month, job_count DESC;

\echo '=== Phase A / BQ29-BQ32: Company + portal demand ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    c.company_name,
    p.portal_name,
    COUNT(*) AS job_count
FROM fact_job f
JOIN dim_company c ON c.company_id = f.company_id
JOIN dim_portal p ON p.portal_id = f.portal_id
GROUP BY COALESCE(c.industry, 'Unknown'), c.company_name, p.portal_name
ORDER BY job_count DESC
LIMIT 30;

-- ---------
-- Phase B
-- ---------
\echo '=== Phase B / BQ11-BQ12: Skill popularity and salary ==='
SELECT
    s.skill_name,
    COUNT(*) AS demand_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM bridge_job_skill b
JOIN dim_skill s ON s.skill_id = b.skill_id
JOIN fact_job f ON f.fact_job_id = b.fact_job_id
GROUP BY s.skill_name
ORDER BY demand_count DESC, avg_salary DESC NULLS LAST
LIMIT 30;

\echo '=== Phase B / BQ15-BQ16: Top skills by industry + time ==='
SELECT
    t.year,
    t.month,
    COALESCE(c.industry, 'Unknown') AS industry,
    s.skill_name,
    COUNT(*) AS demand_count
FROM bridge_job_skill b
JOIN fact_job f ON f.fact_job_id = b.fact_job_id
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_company c ON c.company_id = f.company_id
JOIN dim_skill s ON s.skill_id = b.skill_id
GROUP BY t.year, t.month, COALESCE(c.industry, 'Unknown'), s.skill_name
ORDER BY t.year, t.month, demand_count DESC;

\echo '=== Phase B / BQ52-BQ53: Benefit popularity and salary ==='
SELECT
    be.benefit_name,
    COUNT(*) AS demand_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM bridge_job_benefit bb
JOIN dim_benefit be ON be.benefit_id = bb.benefit_id
JOIN fact_job f ON f.fact_job_id = bb.fact_job_id
GROUP BY be.benefit_name
ORDER BY demand_count DESC, avg_salary DESC NULLS LAST
LIMIT 30;

-- ---------
-- Phase C
-- ---------
\echo '=== Phase C / BQ48-BQ49-BQ50: Experience slices ==='
SELECT
    j.work_type,
    j.qualification,
    f.min_experience_years,
    f.max_experience_years,
    COUNT(*) AS job_count
FROM fact_job f
JOIN dim_job j ON j.job_dim_id = f.job_dim_id
GROUP BY j.work_type, j.qualification, f.min_experience_years, f.max_experience_years
ORDER BY job_count DESC
LIMIT 40;

\echo '=== Phase C / BQ56-BQ57: Cost effectiveness by country ==='
WITH skill_density AS (
    SELECT
        f.location_id,
        COUNT(*)::NUMERIC / NULLIF(COUNT(DISTINCT f.fact_job_id), 0) AS avg_skills_per_job
    FROM fact_job f
    LEFT JOIN bridge_job_skill b ON b.fact_job_id = f.fact_job_id
    GROUP BY f.location_id
)
SELECT
    l.country,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary,
    AVG(sd.avg_skills_per_job) AS avg_skills_per_job,
    AVG(sd.avg_skills_per_job) / NULLIF(AVG((f.min_salary + f.max_salary) / 2.0), 0) AS skill_per_salary_ratio
FROM fact_job f
JOIN dim_location l ON l.location_id = f.location_id
JOIN skill_density sd ON sd.location_id = f.location_id
GROUP BY l.country
ORDER BY skill_per_salary_ratio DESC NULLS LAST, job_count DESC
LIMIT 20;

-- -------------
-- Materialized views for dashboard speed
-- -------------
DROP MATERIALIZED VIEW IF EXISTS mv_salary_geo;
CREATE MATERIALIZED VIEW mv_salary_geo AS
SELECT
    l.country,
    l.city,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.country, l.city;

CREATE INDEX IF NOT EXISTS idx_mv_salary_geo_country_city
ON mv_salary_geo (country, city);

DROP MATERIALIZED VIEW IF EXISTS mv_skill_demand_month;
CREATE MATERIALIZED VIEW mv_skill_demand_month AS
SELECT
    t.year,
    t.month,
    s.skill_name,
    COUNT(*) AS demand_count
FROM bridge_job_skill b
JOIN fact_job f ON f.fact_job_id = b.fact_job_id
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_skill s ON s.skill_id = b.skill_id
GROUP BY t.year, t.month, s.skill_name;

CREATE INDEX IF NOT EXISTS idx_mv_skill_demand_month
ON mv_skill_demand_month (year, month, skill_name);

-- Refresh after each ETL run:
-- REFRESH MATERIALIZED VIEW mv_salary_geo;
-- REFRESH MATERIALIZED VIEW mv_skill_demand_month;

