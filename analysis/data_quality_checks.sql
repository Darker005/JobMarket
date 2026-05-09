-- =======================================================
-- Data quality checks after ETL
-- Purpose: prove row volume, completeness, and referential integrity
-- =======================================================

\echo '=== [DQ-1] Row count checks ==='
SELECT 'fact_job' AS table_name, COUNT(*) AS row_count FROM fact_job
UNION ALL
SELECT 'bridge_job_skill', COUNT(*) FROM bridge_job_skill
UNION ALL
SELECT 'bridge_job_benefit', COUNT(*) FROM bridge_job_benefit
UNION ALL
SELECT 'dim_time', COUNT(*) FROM dim_time
UNION ALL
SELECT 'dim_location', COUNT(*) FROM dim_location
UNION ALL
SELECT 'dim_company', COUNT(*) FROM dim_company
UNION ALL
SELECT 'dim_job', COUNT(*) FROM dim_job
UNION ALL
SELECT 'dim_portal', COUNT(*) FROM dim_portal
UNION ALL
SELECT 'dim_preference', COUNT(*) FROM dim_preference
UNION ALL
SELECT 'dim_skill', COUNT(*) FROM dim_skill
UNION ALL
SELECT 'dim_benefit', COUNT(*) FROM dim_benefit;

\echo '=== [DQ-2] Null checks on required fact columns ==='
SELECT
  COUNT(*) AS total_fact_rows,
  COUNT(*) FILTER (WHERE job_id IS NULL) AS null_job_id,
  COUNT(*) FILTER (WHERE time_id IS NULL) AS null_time_id,
  COUNT(*) FILTER (WHERE location_id IS NULL) AS null_location_id,
  COUNT(*) FILTER (WHERE company_id IS NULL) AS null_company_id,
  COUNT(*) FILTER (WHERE job_dim_id IS NULL) AS null_job_dim_id,
  COUNT(*) FILTER (WHERE portal_id IS NULL) AS null_portal_id,
  COUNT(*) FILTER (WHERE preference_id IS NULL) AS null_preference_id
FROM fact_job;

\echo '=== [DQ-3] Domain checks (salary and experience range sanity) ==='
SELECT
  COUNT(*) FILTER (
    WHERE min_salary IS NOT NULL AND max_salary IS NOT NULL AND min_salary > max_salary
  ) AS bad_salary_ranges,
  COUNT(*) FILTER (
    WHERE min_experience_years IS NOT NULL AND max_experience_years IS NOT NULL
      AND min_experience_years > max_experience_years
  ) AS bad_experience_ranges
FROM fact_job;

\echo '=== [DQ-4] Geographic validity checks ==='
SELECT
  COUNT(*) FILTER (WHERE l.latitude IS NULL OR l.longitude IS NULL) AS null_coordinates,
  COUNT(*) FILTER (WHERE l.latitude NOT BETWEEN -90 AND 90) AS invalid_latitude,
  COUNT(*) FILTER (WHERE l.longitude NOT BETWEEN -180 AND 180) AS invalid_longitude
FROM dim_location l;

\echo '=== [DQ-5] Referential checks (orphan rows should be 0) ==='
SELECT
  COUNT(*) FILTER (WHERE t.time_id IS NULL) AS orphan_time_fk,
  COUNT(*) FILTER (WHERE l.location_id IS NULL) AS orphan_location_fk,
  COUNT(*) FILTER (WHERE c.company_id IS NULL) AS orphan_company_fk,
  COUNT(*) FILTER (WHERE j.job_dim_id IS NULL) AS orphan_job_fk,
  COUNT(*) FILTER (WHERE p.portal_id IS NULL) AS orphan_portal_fk,
  COUNT(*) FILTER (WHERE pr.preference_id IS NULL) AS orphan_preference_fk
FROM fact_job f
LEFT JOIN dim_time t ON t.time_id = f.time_id
LEFT JOIN dim_location l ON l.location_id = f.location_id
LEFT JOIN dim_company c ON c.company_id = f.company_id
LEFT JOIN dim_job j ON j.job_dim_id = f.job_dim_id
LEFT JOIN dim_portal p ON p.portal_id = f.portal_id
LEFT JOIN dim_preference pr ON pr.preference_id = f.preference_id;

\echo '=== [DQ-6] Bridge integrity checks ==='
SELECT
  COUNT(*) FILTER (WHERE f.fact_job_id IS NULL) AS orphan_bridge_fact_fk,
  COUNT(*) FILTER (WHERE s.skill_id IS NULL) AS orphan_bridge_skill_fk
FROM bridge_job_skill b
LEFT JOIN fact_job f ON f.fact_job_id = b.fact_job_id
LEFT JOIN dim_skill s ON s.skill_id = b.skill_id;

\echo '=== [DQ-7] Benefit bridge integrity checks ==='
SELECT
  COUNT(*) FILTER (WHERE f.fact_job_id IS NULL) AS orphan_benefit_fact_fk,
  COUNT(*) FILTER (WHERE be.benefit_id IS NULL) AS orphan_benefit_dim_fk
FROM bridge_job_benefit bb
LEFT JOIN fact_job f ON f.fact_job_id = bb.fact_job_id
LEFT JOIN dim_benefit be ON be.benefit_id = bb.benefit_id;

\echo '=== [DQ-8] Duplicate checks for business keys ==='
SELECT
  COALESCE(SUM(cnt - 1), 0) AS duplicated_job_ids
FROM (
  SELECT job_id, COUNT(*) AS cnt
  FROM fact_job
  GROUP BY job_id
  HAVING COUNT(*) > 1
) d;

\echo '=== [DQ-9] Quality threshold summary ==='
WITH checks AS (
    SELECT
        COUNT(*) AS total_fact_rows,
        COUNT(*) FILTER (
            WHERE min_salary IS NOT NULL AND max_salary IS NOT NULL AND min_salary > max_salary
        ) AS bad_salary_ranges,
        COUNT(*) FILTER (
            WHERE min_experience_years IS NOT NULL AND max_experience_years IS NOT NULL
              AND min_experience_years > max_experience_years
        ) AS bad_experience_ranges
    FROM fact_job
),
geo AS (
    SELECT
        COUNT(*) FILTER (WHERE latitude NOT BETWEEN -90 AND 90 OR longitude NOT BETWEEN -180 AND 180) AS bad_geo
    FROM dim_location
)
SELECT
    c.total_fact_rows,
    c.bad_salary_ranges,
    c.bad_experience_ranges,
    g.bad_geo,
    CASE
        WHEN c.total_fact_rows = 0 THEN 'FAIL'
        WHEN c.bad_salary_ranges > 0 THEN 'FAIL'
        WHEN c.bad_experience_ranges > 0 THEN 'FAIL'
        WHEN g.bad_geo > 0 THEN 'FAIL'
        ELSE 'PASS'
    END AS dq_status
FROM checks c
CROSS JOIN geo g;
