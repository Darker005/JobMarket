-- =======================================================
-- Data quality checks after ETL
-- Purpose: prove row volume, completeness, and referential integrity
-- =======================================================

\echo '=== [DQ-1] Row count checks ==='
SELECT 'fact_job' AS table_name, COUNT(*) AS row_count FROM fact_job
UNION ALL
SELECT 'bridge_job_skill', COUNT(*) FROM bridge_job_skill
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
SELECT 'dim_skill', COUNT(*) FROM dim_skill;

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

\echo '=== [DQ-4] Referential checks (orphan rows should be 0) ==='
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

\echo '=== [DQ-5] Bridge integrity checks ==='
SELECT
  COUNT(*) FILTER (WHERE f.fact_job_id IS NULL) AS orphan_bridge_fact_fk,
  COUNT(*) FILTER (WHERE s.skill_id IS NULL) AS orphan_bridge_skill_fk
FROM bridge_job_skill b
LEFT JOIN fact_job f ON f.fact_job_id = b.fact_job_id
LEFT JOIN dim_skill s ON s.skill_id = b.skill_id;

\echo '=== [DQ-6] Duplicate checks for business keys ==='
SELECT
  COALESCE(SUM(cnt - 1), 0) AS duplicated_job_ids
FROM (
  SELECT job_id, COUNT(*) AS cnt
  FROM fact_job
  GROUP BY job_id
  HAVING COUNT(*) > 1
) d;
