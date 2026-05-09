-- =========================================
-- 4. INDEXES (OLAP OPTIMIZATION)
-- =========================================

-- =========================================
-- FACT TABLE INDEXES
-- =========================================
CREATE INDEX IF NOT EXISTS idx_fact_source_job
ON fact_job_posting(source_job_id);

CREATE INDEX IF NOT EXISTS idx_fact_time
ON fact_job_posting(time_id);

CREATE INDEX IF NOT EXISTS idx_fact_location
ON fact_job_posting(location_id);

CREATE INDEX IF NOT EXISTS idx_fact_company
ON fact_job_posting(company_id);

CREATE INDEX IF NOT EXISTS idx_fact_job
ON fact_job_posting(job_id);

CREATE INDEX IF NOT EXISTS idx_fact_experience
ON fact_job_posting(experience_id);

CREATE INDEX IF NOT EXISTS idx_fact_qualification
ON fact_job_posting(qualification_id);

CREATE INDEX IF NOT EXISTS idx_fact_work_type
ON fact_job_posting(work_type_id);

CREATE INDEX IF NOT EXISTS idx_fact_preference
ON fact_job_posting(preference_id);

CREATE INDEX IF NOT EXISTS idx_fact_portal
ON fact_job_posting(portal_id);

-- =========================================
-- COMPOSITE INDEXES FOR OLAP
-- =========================================
CREATE INDEX IF NOT EXISTS idx_fact_time_location
ON fact_job_posting(time_id, location_id);

CREATE INDEX IF NOT EXISTS idx_fact_company_time
ON fact_job_posting(company_id, time_id);

CREATE INDEX IF NOT EXISTS idx_fact_job_time
ON fact_job_posting(job_id, time_id);

CREATE INDEX IF NOT EXISTS idx_fact_salary
ON fact_job_posting(min_salary, max_salary);

-- =========================================
-- BRIDGE TABLE INDEXES
-- =========================================

CREATE INDEX IF NOT EXISTS idx_bridge_skill
ON bridge_job_skill(skill_id);

CREATE INDEX IF NOT EXISTS idx_bridge_fact_skill
ON bridge_job_skill(fact_job_id);

CREATE INDEX IF NOT EXISTS idx_bridge_benefit
ON bridge_job_benefit(benefit_id);

CREATE INDEX IF NOT EXISTS idx_bridge_fact_benefit
ON bridge_job_benefit(fact_job_id);
