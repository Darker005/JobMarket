"""Parse analysis/query_olap.sql into runnable statements (skip psql \\echo)."""

from __future__ import annotations

import re
from pathlib import Path

# Nhóm nghiệp vụ + tên hiển thị + mục đích (không dùng tên kiểu "Phase A/B").
# Khóa = chuỗi title y hệt trong file SQL sau \\echo (nội dung trong ngoặc nháy).
_OLAP_LABELS: dict[str, tuple[str, str, str]] = {
    "=== Phase A / BQ1: Country salary ranking ===": (
        "Lương & phân khúc thị trường",
        "Lương trung bình theo quốc gia",
        "So sánh mức lương giữa các quốc gia để xác định thị trường trả cao hoặc thấp hơn.",
    ),
    "=== Phase A / BQ2: City salary ranking ===": (
        "Địa lý & phân bổ địa điểm",
        "BQ16 — Lương theo thành phố (city ranking)",
        "Theo catalog: BQ16 location salary; echo cũ ghi BQ2 city — nội dung là xếp hạng lương theo city/country.",
    ),
    "=== Phase A / BQ3-BQ4: Industry/Sector salary ===": (
        "Lương & phân khúc thị trường",
        "Lương theo ngành và lĩnh vực",
        "Đối chiếu mức lương theo industry/sector để hướng chiến lược ngành.",
    ),
    "=== Phase A / BQ5: Work type salary ===": (
        "Lương & phân khúc thị trường",
        "Lương theo hình thức làm việc",
        "So sánh full-time / part-time / intern / … về mức lương trung bình.",
    ),
    "=== Phase A / BQ21-BQ24-BQ36-BQ38: Monthly trend ===": (
        "Xu hướng & thời điểm đăng tin",
        "Số tin và lương theo tháng và quốc gia",
        "Theo dõi nhu cầu tuyển dụng và mức lương theo thời gian để làm biểu đồ xu hướng.",
    ),
    "=== Phase A / BQ29-BQ32: Company + portal demand ===": (
        "Doanh nghiệp & nền tảng tuyển dụng",
        "Nhu cầu tuyển theo công ty, ngành và job portal",
        "Tìm công ty/portal đăng nhiều tin nhất phục vụ phân tích kênh và đối thủ.",
    ),
    "=== Phase B / BQ11-BQ12: Skill popularity and salary ===": (
        "Kỹ năng",
        "Độ hot của kỹ năng và lương kèm theo",
        "Kỹ năng nào xuất hiện nhiều và gắn với mức lương trung bình ra sao.",
    ),
    "=== Phase B / BQ15-BQ16: Top skills by industry + time ===": (
        "Kỹ năng",
        "Kỹ năng theo ngành và theo thời gian",
        "Xem ngành nào đang cần skill gì mạnh nhất theo từng tháng.",
    ),
    "=== Phase B / BQ52-BQ53: Benefit popularity and salary ===": (
        "Phúc lợi",
        "Phúc lợi phổ biến và mức lương đi kèm",
        "Ưu đãi nào hay gặp và có tương quan với lương cao hơn hay không.",
    ),
    "=== Phase C / BQ48-BQ49-BQ50: Experience slices ===": (
        "Kinh nghiệm & yêu cầu hồ sơ",
        "Mốc kinh nghiệm theo loại việc và bằng cấp",
        "Phân bổ số tin theo khoảng năm kinh nghiệm, work type và qualification.",
    ),
    "=== Phase C / BQ56-BQ57: Cost effectiveness by country ===": (
        "Hiệu quả chi phí & mật độ kỹ năng",
        "Tỷ lệ kỹ năng trên đồng lương theo quốc gia",
        "Gợi ý thị trường nào có nhiều skill ghi nhận trên mỗi đơn vị lương (tín hiệu cost-effectiveness thô).",
    ),
}


def _ddl_label(sql: str) -> tuple[str, str, str]:
    s = sql.strip()
    u = s.upper()
    group = "Bảo trì CSDL (tốc độ truy vấn)"
    if "MV_SALARY_GEO" in u:
        if u.startswith("DROP"):
            return (
                group,
                "Xóa materialized view: lương theo quốc gia/thành phố",
                "Chuẩn bị tạo lại view tổng hợp geo + lương; chạy trước CREATE khi cần refresh cấu trúc.",
            )
        if "MATERIALIZED VIEW" in u:
            return (
                group,
                "Tạo lại MV: tổng hợp lương & số tin theo geo",
                "Tăng tốc dashboard/map và truy vấn lọc theo quốc gia–thành phố sau mỗi lần nạp dữ liệu.",
            )
        if "INDEX" in u:
            return (
                group,
                "Index cho MV geo",
                "Hỗ trợ lọc nhanh theo country/city trên bảng tổng hợp.",
            )
    if "MV_SKILL_DEMAND_MONTH" in u or "SKILL_DEMAND_MONTH" in u:
        if u.startswith("DROP"):
            return (
                group,
                "Xóa materialized view: nhu cầu skill theo tháng",
                "Chuẩn bị tạo lại view xu hướng skill theo thời gian.",
            )
        if "MATERIALIZED VIEW" in u:
            return (
                group,
                "Tạo lại MV: nhu cầu skill theo năm–tháng",
                "Tăng tốc biểu đồ xu hướng skill và báo cáo theo kỳ.",
            )
        if "INDEX" in u:
            return (
                group,
                "Index cho MV skill theo tháng",
                "Hỗ trợ lọc nhanh theo year/month/skill.",
            )
    return (
        group,
        "Lệnh DDL (DROP/CREATE)",
        "Thao tác trên CSDL: chỉ chạy khi bạn hiểu rõ tác động.",
    )


def _annotate_from_bq_echo(title: str) -> tuple[str, str, str] | None:
    """Titles dạng '=== BQ4: ... ===' trong query_bq_gaps.sql."""
    if not re.search(r"BQ\s*\d+", title, re.I):
        return None
    name = re.sub(r"^===\s*|\s*===\s*$", "", title.strip()).strip()
    m = re.search(r"BQ\s*(\d+)", title, re.I)
    n = int(m.group(1)) if m else 0
    if 1 <= n <= 8:
        g = "Lương & phân khúc thị trường"
    elif 9 <= n <= 14:
        g = "Kỹ năng"
    elif 15 <= n <= 19:
        g = "Địa lý & phân bổ địa điểm"
    elif 20 <= n <= 25:
        g = "Doanh nghiệp & nền tảng tuyển dụng"
    elif 26 <= n <= 31:
        g = "Xu hướng & thời điểm đăng tin"
    elif 32 <= n <= 35:
        g = "Phúc lợi"
    elif 36 <= n <= 39:
        g = "Kinh nghiệm & yêu cầu hồ sơ"
    elif 40 <= n <= 41:
        g = "Dự báo (Python)"
    elif 42 <= n <= 43:
        g = "Nâng cao (ngoài SQL)"
    else:
        g = "Khác"
    return (g, name[:200], "Theo catalog BQ — xem docs/bq_coverage.md.")


def _annotate(title: str, kind: str, sql: str) -> tuple[str, str, str]:
    if kind == "olap" and title in _OLAP_LABELS:
        return _OLAP_LABELS[title]
    if kind == "olap":
        cat = _annotate_from_bq_echo(title)
        if cat:
            return cat
    if kind == "ddl":
        return _ddl_label(sql)
    return (
        "Khác",
        title.strip("= ").replace("=== ", "")[:120],
        "Truy vấn từ file OLAP; bổ sung mô tả trong query_loader nếu cần.",
    )


def _strip_echo_title(first_line: str) -> str | None:
    line = first_line.strip()
    m = re.match(r"^['\"](.+)['\"]\s*$", line)
    if m:
        return m.group(1)
    return None


def _split_sql_statements(block: str) -> list[str]:
    """Split on semicolon + newline; keep statements that look like SQL."""
    parts = re.split(r";\s*\n", block.strip())
    out: list[str] = []
    for p in parts:
        s = p.strip()
        if not s:
            continue
        lines = [ln for ln in s.splitlines() if not ln.strip().startswith("--")]
        s2 = "\n".join(lines).strip()
        if not s2:
            continue
        upper = s2.upper()
        if upper.startswith("SELECT") or upper.startswith("WITH"):
            out.append(s2 if s2.endswith(";") else s2 + ";")
        elif upper.startswith("DROP ") or upper.startswith("CREATE "):
            out.append(s2 if s2.endswith(";") else s2 + ";")
    return out


def load_queries_from_olap_sql(sql_path: Path) -> list[dict]:
    text = sql_path.read_text(encoding="utf-8")
    chunks = re.split(r"^\s*\\echo\s+", text, flags=re.MULTILINE)
    queries: list[dict] = []
    qid = 0

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        lines = chunk.splitlines()
        if not lines:
            continue
        title = _strip_echo_title(lines[0])
        if title is None:
            continue
        body = "\n".join(lines[1:]).strip()

        for stmt in _split_sql_statements(body):
            upper = stmt.upper()
            if upper.startswith("SELECT") or upper.startswith("WITH"):
                kind = "olap"
            elif upper.startswith("DROP ") or upper.startswith("CREATE "):
                kind = "ddl"
            else:
                kind = "other"
            qid += 1
            group, name, purpose = _annotate(title, kind, stmt)
            queries.append(
                {
                    "id": qid,
                    "source_title": title,
                    "group": group,
                    "name": name,
                    "purpose": purpose,
                    "kind": kind,
                    "sql": stmt,
                }
            )
    return queries


def load_merged_catalog(paths: list[Path]) -> list[dict]:
    merged: list[dict] = []
    for p in paths:
        merged.extend(load_queries_from_olap_sql(p))
    for i, q in enumerate(merged, start=1):
        q["id"] = i
    return merged


GROUP_DISPLAY_ORDER: list[str] = [
    "Lương & phân khúc thị trường",
    "Địa lý & phân bổ địa điểm",
    "Xu hướng & thời điểm đăng tin",
    "Doanh nghiệp & nền tảng tuyển dụng",
    "Kỹ năng",
    "Phúc lợi",
    "Kinh nghiệm & yêu cầu hồ sơ",
    "Hiệu quả chi phí & mật độ kỹ năng",
    "Dự báo (Python)",
    "Nâng cao (ngoài SQL)",
    "Bảo trì CSDL (tốc độ truy vấn)",
]


def ordered_groups(groups: set[str]) -> list[str]:
    def sort_key(g: str) -> tuple[int, str]:
        if g in GROUP_DISPLAY_ORDER:
            return (GROUP_DISPLAY_ORDER.index(g), g)
        return (999, g)

    return sorted(groups, key=sort_key)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
