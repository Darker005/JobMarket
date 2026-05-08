-- FACT TABLE INDEXES
CREATE INDEX idx_fact_time ON fact_job_posting(time_id);
CREATE INDEX idx_fact_location ON fact_job_posting(location_id);
CREATE INDEX idx_fact_company ON fact_job_posting(company_id);
CREATE INDEX idx_fact_job ON fact_job_posting(job_id);
CREATE INDEX idx_fact_portal ON fact_job_posting(portal_id);

-- BRIDGE INDEX
CREATE INDEX idx_bridge_skill ON bridge_job_skill(skill_id);