-- tạo index
CREATE INDEX idx_fact_time ON fact_job(time_id);
CREATE INDEX idx_fact_location ON fact_job(location_id);
CREATE INDEX idx_fact_company ON fact_job(company_id);
CREATE INDEX idx_fact_job_dim ON fact_job(job_dim_id);
CREATE INDEX idx_fact_portal ON fact_job(portal_id);
CREATE INDEX idx_fact_preference ON fact_job(preference_id);
CREATE INDEX idx_bridge_skill ON bridge_job_skill(skill_id);
CREATE INDEX idx_bridge_benefit ON bridge_job_benefit(benefit_id);
CREATE INDEX idx_fact_job_id ON fact_job(job_id);
