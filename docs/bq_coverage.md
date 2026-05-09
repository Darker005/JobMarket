# Đối chiếu Business Questions (BQ1–BQ43) với code

**Quy ước lương:** `avg_salary = (min_salary + max_salary) / 2` (không có cột `avg_salary` trên fact).

| BQ | Mô tả ngắn | Trạng thái | Nơi chạy |
|----|------------|------------|-----------|
| BQ1 | Country lương cao | Có | `query_olap.sql` |
| BQ2 | Industry lương cao | Có | `query_bq_gaps.sql` |
| BQ3 | Work type lương | Có | `query_olap.sql` |
| BQ4 | Qualification vs salary | Có | `query_bq_gaps.sql` |
| BQ5 | Experience vs salary | Có | `query_bq_gaps.sql` |
| BQ6 | Role/job salary cao | Có | `query_bq_gaps.sql` |
| BQ7 | Company size vs salary | Có | `query_bq_gaps.sql` |
| BQ8 | Preference vs salary | Có | `query_bq_gaps.sql` |
| BQ9 | Skill phổ biến (count) | Có | `query_bq_gaps.sql` |
| BQ10 | Skill lương cao | Có (gộp demand + avg salary) | `query_olap.sql` |
| BQ11 | Skill combinations | Có | `query_bq_gaps.sql` |
| BQ12 | Industry nhiều skill | Có | `query_bq_gaps.sql` |
| BQ13 | Top skills theo industry | Có | `query_bq_gaps.sql` |
| BQ14 | Skill demand theo thời gian | Có | `query_olap.sql` + MV |
| BQ15 | Country nhiều jobs | Có | `query_bq_gaps.sql` |
| BQ16 | Location lương cao | Có (city ranking, HAVING ≥5) | `query_olap.sql` *(echo cũ “BQ2 city” — nội dung = BQ16)* |
| BQ17 | Hiring trend time + country | Có | `query_olap.sql` |
| BQ18 | Work type theo location | Có | `query_bq_gaps.sql` |
| BQ19 | Remote tập trung đâu | Có *(heuristic `ILIKE '%remote%'`* | `query_bq_gaps.sql` |
| BQ20 | Industry hiring demand | Có | `query_bq_gaps.sql` |
| BQ21 | Sector trend theo thời gian | Có | `query_bq_gaps.sql` |
| BQ22 | Top companies | Có | `query_bq_gaps.sql` |
| BQ23 | Portal nhiều jobs | Có | `query_bq_gaps.sql` |
| BQ24 | Portal theo role | Có | `query_bq_gaps.sql` |
| BQ25 | Industry hiring diversity | Có | `query_bq_gaps.sql` |
| BQ26 | Postings theo năm | Có | `query_bq_gaps.sql` |
| BQ27 | Salary trend theo thời gian | Có | `query_bq_gaps.sql` |
| BQ28 | Skill demand trend | Có | MV `mv_skill_demand_month` |
| BQ29 | Industry hiring trend theo thời gian | Có | `query_bq_gaps.sql` |
| BQ30 | Top growing industries | Có *(YoY đơn giản: năm max vs năm trước)* | `query_bq_gaps.sql` |
| BQ31 | Top growing skills | Có *(YoY đơn giản)* | `query_bq_gaps.sql` |
| BQ32 | Benefit phổ biến | Có (gộp với avg salary) | `query_olap.sql` |
| BQ33 | Benefit vs salary | Có (cùng query BQ32) | `query_olap.sql` |
| BQ34 | Industry nhiều benefits | Có | `query_bq_gaps.sql` |
| BQ35 | Company size vs benefits | Có | `query_bq_gaps.sql` |
| BQ36 | Preference theo role | Có | `query_bq_gaps.sql` |
| BQ37 | Qualification theo industry | Có | `query_bq_gaps.sql` |
| BQ38 | Experience level demand | Có | `query_bq_gaps.sql` |
| BQ39 | Experience vs work type | Có | `query_olap.sql` + `query_bq_gaps.sql` (bản tập trung) |
| BQ40 | Predict salary | Có (Python) | `predictive_prototype.py` |
| BQ41 | Predict hot skills | Một phần (Python forecast) | `predictive_prototype.py` |
| BQ42 | Job similarity | Thiếu *(engine / scoring ngoài SQL ad-hoc)* | — |
| BQ43 | Recommendation | Thiếu *(hệ gợi ý đầy đủ)* | — |

**Thiếu thực sự trong repo:** chỉ **BQ42**, **BQ43** (và có thể mở rộng độ tin cậy BQ41 so với mô tả “hot skills”).

Pipeline: `query_olap.sql` rồi `query_bq_gaps.sql` (`run.py`, `run.sh`). Streamlit nạp cả hai qua `load_merged_catalog`.
