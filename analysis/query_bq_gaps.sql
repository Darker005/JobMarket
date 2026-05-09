-- =======================================================
-- BQ catalog — các câu SQL bổ sung (đối chiếu docs/bq_coverage.md)
-- Chạy sau query_olap.sql. avg_salary = (min_salary+max_salary)/2
-- =======================================================

\echo '=== BQ2: Industry — lương trung bình cao nhất ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.industry, 'Unknown')
ORDER BY avg_salary DESC NULLS LAST, job_count DESC
LIMIT 25;

\echo '=== BQ4: Qualification vs salary ==='
SELECT
    q.qualification_name,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_qualification q ON q.qualification_id = f.qualification_id
GROUP BY q.qualification_name
ORDER BY avg_salary DESC NULLS LAST, job_count DESC;

\echo '=== BQ5: Experience vs salary ==='
SELECT
    ex.experience_text,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_experience ex ON ex.experience_id = f.experience_id
GROUP BY ex.experience_text
ORDER BY avg_salary DESC NULLS LAST, job_count DESC
LIMIT 30;

\echo '=== BQ6: Job title / role — lương cao (đủ mẫu) ==='
SELECT
    j.job_title,
    COALESCE(j.role, '') AS role,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_job j ON j.job_id = f.job_id
GROUP BY j.job_title, j.role
HAVING COUNT(*) >= 5
ORDER BY avg_salary DESC NULLS LAST
LIMIT 25;

\echo '=== BQ7: Company size vs salary ==='
SELECT
    COALESCE(c.company_size, 'Unknown') AS company_size,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.company_size, 'Unknown')
ORDER BY avg_salary DESC NULLS LAST, job_count DESC;

\echo '=== BQ8: Preference vs salary ==='
SELECT
    pr.preference_name,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_preference pr ON pr.preference_id = f.preference_id
GROUP BY pr.preference_name
ORDER BY avg_salary DESC NULLS LAST, job_count DESC;

\echo '=== BQ9: Skill phổ biến nhất (số tin) ==='
SELECT
    s.skill_name,
    COUNT(DISTINCT b.fact_job_id) AS job_postings_with_skill
FROM bridge_job_skill b
JOIN dim_skill s ON s.skill_id = b.skill_id
GROUP BY s.skill_name
ORDER BY job_postings_with_skill DESC
LIMIT 30;

\echo '=== BQ11: Cặp skill cùng xuất hiện trong một tin (top co-occurrence) ==='
SELECT
    s1.skill_name AS skill_a,
    s2.skill_name AS skill_b,
    COUNT(*) AS pair_count
FROM bridge_job_skill b1
JOIN bridge_job_skill b2
    ON b1.fact_job_id = b2.fact_job_id
   AND b1.skill_id < b2.skill_id
JOIN dim_skill s1 ON s1.skill_id = b1.skill_id
JOIN dim_skill s2 ON s2.skill_id = b2.skill_id
GROUP BY s1.skill_name, s2.skill_name
ORDER BY pair_count DESC
LIMIT 30;

\echo '=== BQ12: Industry — tổng lượt gắn skill (volume) ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(b.skill_id) AS skill_link_rows
FROM bridge_job_skill b
JOIN fact_job_posting f ON f.fact_job_id = b.fact_job_id
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.industry, 'Unknown')
ORDER BY skill_link_rows DESC
LIMIT 25;

\echo '=== BQ13: Top 5 skill theo từng industry (theo volume) ==='
WITH ranked AS (
    SELECT
        COALESCE(c.industry, 'Unknown') AS industry,
        s.skill_name,
        COUNT(*) AS cnt,
        ROW_NUMBER() OVER (
            PARTITION BY COALESCE(c.industry, 'Unknown')
            ORDER BY COUNT(*) DESC
        ) AS rn
    FROM bridge_job_skill b
    JOIN fact_job_posting f ON f.fact_job_id = b.fact_job_id
    JOIN dim_company c ON c.company_id = f.company_id
    JOIN dim_skill s ON s.skill_id = b.skill_id
    GROUP BY COALESCE(c.industry, 'Unknown'), s.skill_name
)
SELECT industry, skill_name, cnt
FROM ranked
WHERE rn <= 5
ORDER BY industry, cnt DESC;

\echo '=== BQ15: Country — số tin tuyển nhiều nhất ==='
SELECT
    l.country,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_location l ON l.location_id = f.location_id
GROUP BY l.country
ORDER BY job_count DESC
LIMIT 25;

\echo '=== BQ18: Phân bổ work type theo quốc gia ==='
SELECT
    l.country,
    wt.work_type_name,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_location l ON l.location_id = f.location_id
JOIN dim_work_type wt ON wt.work_type_id = f.work_type_id
GROUP BY l.country, wt.work_type_name
ORDER BY l.country, job_count DESC;

\echo '=== BQ19: Remote — tập trung theo quốc gia (work_type chứa remote) ==='
SELECT
    l.country,
    COUNT(*) AS remoteish_jobs
FROM fact_job_posting f
JOIN dim_location l ON l.location_id = f.location_id
JOIN dim_work_type wt ON wt.work_type_id = f.work_type_id
WHERE wt.work_type_name ILIKE '%remote%'
GROUP BY l.country
ORDER BY remoteish_jobs DESC;

\echo '=== BQ20: Industry — tổng số tin (hiring demand) ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.industry, 'Unknown')
ORDER BY job_count DESC
LIMIT 25;

\echo '=== BQ21: Sector — xu hướng theo tháng ==='
SELECT
    t.year,
    t.month,
    COALESCE(c.sector, 'Unknown') AS sector,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY t.year, t.month, COALESCE(c.sector, 'Unknown')
ORDER BY t.year, t.month, job_count DESC;

\echo '=== BQ22: Top companies theo số tin ==='
SELECT
    c.company_name,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY c.company_name
ORDER BY job_count DESC
LIMIT 25;

\echo '=== BQ23: Portal — số tin ==='
SELECT
    p.portal_name,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_portal p ON p.portal_id = f.portal_id
GROUP BY p.portal_name
ORDER BY job_count DESC;

\echo '=== BQ24: Portal theo role ==='
SELECT
    p.portal_name,
    COALESCE(j.role, '') AS role,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_portal p ON p.portal_id = f.portal_id
JOIN dim_job j ON j.job_id = f.job_id
GROUP BY p.portal_name, j.role
ORDER BY job_count DESC
LIMIT 40;

\echo '=== BQ25: Industry — đa dạng hóa vị trí (đếm dim_job khác nhau) ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(DISTINCT f.job_id) AS distinct_job_profiles,
    COUNT(*) AS job_postings
FROM fact_job_posting f
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.industry, 'Unknown')
ORDER BY distinct_job_profiles DESC;

\echo '=== BQ26: Số tin theo năm ==='
SELECT
    t.year,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_time t ON t.time_id = f.time_id
GROUP BY t.year
ORDER BY t.year;

\echo '=== BQ27: Lương trung bình theo tháng ==='
SELECT
    t.year,
    t.month,
    COUNT(*) AS job_count,
    AVG((f.min_salary + f.max_salary) / 2.0) AS avg_salary
FROM fact_job_posting f
JOIN dim_time t ON t.time_id = f.time_id
GROUP BY t.year, t.month
ORDER BY t.year, t.month;

\echo '=== BQ29: Industry — hiring theo tháng ==='
SELECT
    t.year,
    t.month,
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_time t ON t.time_id = f.time_id
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY t.year, t.month, COALESCE(c.industry, 'Unknown')
ORDER BY t.year, t.month, job_count DESC;

\echo '=== BQ30: Industry — tăng số tin (năm mới nhất vs năm liền trước, đơn giản) ==='
WITH industry_year AS (
    SELECT
        COALESCE(c.industry, 'Unknown') AS ind,
        t.year AS yr,
        COUNT(*)::NUMERIC AS cnt
    FROM fact_job_posting f
    JOIN dim_time t ON t.time_id = f.time_id
    JOIN dim_company c ON c.company_id = f.company_id
    GROUP BY COALESCE(c.industry, 'Unknown'), t.year
),
bounds AS (
    SELECT MAX(yr) AS y2 FROM industry_year
)
SELECT
    y2.ind,
    COALESCE(y1.cnt, 0) AS jobs_prior_year,
    y2.cnt AS jobs_latest_year,
    y2.cnt - COALESCE(y1.cnt, 0) AS growth
FROM industry_year y2
LEFT JOIN industry_year y1
    ON y1.ind = y2.ind
   AND y1.yr = (SELECT y2 - 1 FROM bounds)
WHERE y2.yr = (SELECT y2 FROM bounds)
ORDER BY growth DESC NULLS LAST
LIMIT 20;

\echo '=== BQ31: Skill — tăng demand (năm mới nhất vs năm liền trước, đơn giản) ==='
WITH skill_year AS (
    SELECT
        s.skill_name AS sk,
        t.year AS yr,
        COUNT(*)::NUMERIC AS cnt
    FROM bridge_job_skill b
    JOIN fact_job_posting f ON f.fact_job_id = b.fact_job_id
    JOIN dim_time t ON t.time_id = f.time_id
    JOIN dim_skill s ON s.skill_id = b.skill_id
    GROUP BY s.skill_name, t.year
),
bounds AS (
    SELECT MAX(yr) AS y2 FROM skill_year
)
SELECT
    y2.sk AS skill_name,
    COALESCE(y1.cnt, 0) AS mentions_prior_year,
    y2.cnt AS mentions_latest_year,
    y2.cnt - COALESCE(y1.cnt, 0) AS growth
FROM skill_year y2
LEFT JOIN skill_year y1
    ON y1.sk = y2.sk
   AND y1.yr = (SELECT y2 - 1 FROM bounds)
WHERE y2.yr = (SELECT y2 FROM bounds)
ORDER BY growth DESC NULLS LAST
LIMIT 20;

\echo '=== BQ34: Industry — độ phong phú benefit (distinct + link count) ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    COUNT(DISTINCT bb.benefit_id) AS distinct_benefits,
    COUNT(*) AS benefit_links
FROM bridge_job_benefit bb
JOIN fact_job_posting f ON f.fact_job_id = bb.fact_job_id
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.industry, 'Unknown')
ORDER BY distinct_benefits DESC, benefit_links DESC
LIMIT 20;

\echo '=== BQ35: Company size vs số loại benefit ==='
SELECT
    COALESCE(c.company_size, 'Unknown') AS company_size,
    COUNT(DISTINCT bb.benefit_id) AS distinct_benefits,
    COUNT(*) AS benefit_links
FROM bridge_job_benefit bb
JOIN fact_job_posting f ON f.fact_job_id = bb.fact_job_id
JOIN dim_company c ON c.company_id = f.company_id
GROUP BY COALESCE(c.company_size, 'Unknown')
ORDER BY distinct_benefits DESC;

\echo '=== BQ36: Preference theo role ==='
SELECT
    pr.preference_name,
    COALESCE(j.role, '') AS role,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_preference pr ON pr.preference_id = f.preference_id
JOIN dim_job j ON j.job_id = f.job_id
GROUP BY pr.preference_name, j.role
ORDER BY job_count DESC
LIMIT 40;

\echo '=== BQ37: Qualification phổ biến theo industry ==='
SELECT
    COALESCE(c.industry, 'Unknown') AS industry,
    q.qualification_name,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_company c ON c.company_id = f.company_id
JOIN dim_qualification q ON q.qualification_id = f.qualification_id
GROUP BY COALESCE(c.industry, 'Unknown'), q.qualification_name
ORDER BY industry, job_count DESC
LIMIT 60;

\echo '=== BQ38: Experience — mức demand (số tin) ==='
SELECT
    ex.experience_text,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_experience ex ON ex.experience_id = f.experience_id
GROUP BY ex.experience_text
ORDER BY job_count DESC
LIMIT 30;

\echo '=== BQ39: Experience vs work type (tổng hợp) ==='
SELECT
    ex.experience_text,
    wt.work_type_name,
    COUNT(*) AS job_count
FROM fact_job_posting f
JOIN dim_experience ex ON ex.experience_id = f.experience_id
JOIN dim_work_type wt ON wt.work_type_id = f.work_type_id
GROUP BY ex.experience_text, wt.work_type_name
ORDER BY job_count DESC
LIMIT 40;
