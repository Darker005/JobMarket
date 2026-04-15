-- =======================================================
-- Query & OLAP checklist + runnable SQL for report/demo
-- =======================================================
-- Run after: etl/run_all.sql (or after create_tables + staging + transform)

-- 0) Data quality sanity checks
SELECT COUNT(*) AS total_fact_rows FROM fact_job;
SELECT COUNT(*) AS total_skills_bridge_rows FROM bridge_job_skill;
SELECT COUNT(*) AS total_time_rows FROM dim_time;

-- =======================================================
-- 1) OLAP by Time (trend)
-- =======================================================
-- 1.1 Number of jobs by month
SELECT
    t.year,
    t.month,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
GROUP BY t.year, t.month
ORDER BY t.year, t.month;

-- 1.2 Average salary range by quarter
SELECT
    t.year,
    t.quarter,
    AVG(f.min_salary) AS avg_min_salary,
    AVG(f.max_salary) AS avg_max_salary
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
GROUP BY t.year, t.quarter
ORDER BY t.year, t.quarter;

-- =======================================================
-- 2) OLAP by Geography
-- =======================================================
-- 2.1 Top countries by job count
SELECT
    l.country,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.country
ORDER BY total_jobs DESC
LIMIT 15;

-- 2.2 Salary heatmap base: country + city
SELECT
    l.country,
    l.city,
    COUNT(*) AS total_jobs,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_mid_salary
FROM fact_job f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.country, l.city
ORDER BY total_jobs DESC, avg_mid_salary DESC
LIMIT 30;

-- =======================================================
-- 3) OLAP by Job attributes
-- =======================================================
-- 3.1 Top job titles
SELECT
    j.job_title,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_job j ON j.job_dim_id = f.job_dim_id
GROUP BY j.job_title
ORDER BY total_jobs DESC
LIMIT 20;

-- 3.2 Work type distribution
SELECT
    COALESCE(j.work_type, 'Unknown') AS work_type,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_job j ON j.job_dim_id = f.job_dim_id
GROUP BY COALESCE(j.work_type, 'Unknown')
ORDER BY total_jobs DESC;

-- 3.3 Qualification vs salary
SELECT
    COALESCE(j.qualification, 'Unknown') AS qualification,
    COUNT(*) AS total_jobs,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_mid_salary
FROM fact_job f
JOIN dim_job j ON j.job_dim_id = f.job_dim_id
GROUP BY COALESCE(j.qualification, 'Unknown')
ORDER BY avg_mid_salary DESC NULLS LAST, total_jobs DESC;

-- =======================================================
-- 4) OLAP by Source channel (portal/preference)
-- =======================================================
-- 4.1 Portal performance
SELECT
    p.portal_name,
    COUNT(*) AS total_jobs,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_mid_salary
FROM fact_job f
JOIN dim_portal p ON p.portal_id = f.portal_id
GROUP BY p.portal_name
ORDER BY total_jobs DESC;

-- 4.2 Preference distribution by portal
SELECT
    p.portal_name,
    pr.preference_name,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_portal p ON p.portal_id = f.portal_id
JOIN dim_preference pr ON pr.preference_id = f.preference_id
GROUP BY p.portal_name, pr.preference_name
ORDER BY p.portal_name, total_jobs DESC;

-- =======================================================
-- 5) Skill analytics (bridge table)
-- =======================================================
-- 5.1 Top skills
SELECT
    s.skill_name,
    COUNT(*) AS jobs_requiring_skill
FROM bridge_job_skill b
JOIN dim_skill s ON s.skill_id = b.skill_id
GROUP BY s.skill_name
ORDER BY jobs_requiring_skill DESC
LIMIT 25;

-- 5.2 Top skills by average salary
SELECT
    s.skill_name,
    COUNT(*) AS jobs_requiring_skill,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_mid_salary
FROM bridge_job_skill b
JOIN dim_skill s ON s.skill_id = b.skill_id
JOIN fact_job f ON f.fact_job_id = b.fact_job_id
GROUP BY s.skill_name
HAVING COUNT(*) >= 20
ORDER BY avg_mid_salary DESC, jobs_requiring_skill DESC
LIMIT 20;

-- =======================================================
-- 6) Multi-dimensional OLAP (slice/dice/drilldown)
-- =======================================================
-- 6.1 Slice: only Full-Time jobs
SELECT
    t.year,
    l.country,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_location l ON l.location_id = f.location_id
JOIN dim_job j ON j.job_dim_id = f.job_dim_id
WHERE j.work_type = 'Full-Time'
GROUP BY t.year, l.country
ORDER BY t.year, total_jobs DESC;

-- 6.2 Dice: 2022-2023 + selected portals
SELECT
    t.year,
    p.portal_name,
    COUNT(*) AS total_jobs,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_mid_salary
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_portal p ON p.portal_id = f.portal_id
WHERE t.year IN (2022, 2023)
  AND p.portal_name IN ('Indeed', 'Glassdoor', 'FlexJobs')
GROUP BY t.year, p.portal_name
ORDER BY t.year, p.portal_name;

-- 6.3 Drilldown: year -> month for top country
WITH top_country AS (
    SELECT l.country
    FROM fact_job f
    JOIN dim_location l ON l.location_id = f.location_id
    GROUP BY l.country
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
SELECT
    t.year,
    t.month,
    l.country,
    COUNT(*) AS total_jobs
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_location l ON l.location_id = f.location_id
JOIN top_country tc ON tc.country = l.country
GROUP BY t.year, t.month, l.country
ORDER BY t.year, t.month;

-- =======================================================
-- 7) Pre-aggregation for dashboard/report speed
-- =======================================================
DROP MATERIALIZED VIEW IF EXISTS mv_jobs_country_month;
CREATE MATERIALIZED VIEW mv_jobs_country_month AS
SELECT
    t.year,
    t.month,
    l.country,
    COUNT(*) AS total_jobs,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_mid_salary
FROM fact_job f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY t.year, t.month, l.country;

CREATE INDEX IF NOT EXISTS idx_mv_jobs_country_month
    ON mv_jobs_country_month (year, month, country);

-- Use this to refresh periodically after ETL:
-- REFRESH MATERIALIZED VIEW mv_jobs_country_month;

