import json
import re
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta

import pandas as pd


RENAME_MAP = {
    "Job Id": "job_id_raw",
    "Experience": "experience_raw",
    "Qualifications": "qualification",
    "Min Salary": "min_salary_raw",
    "Max Salary": "max_salary_raw",
    "location": "city",
    "Country": "country",
    "latitude": "latitude_raw",
    "longitude": "longitude_raw",
    "Work Type": "work_type",
    "Company Size": "company_size",
    "Job Posting Date": "posting_date_raw",
    "Preference": "preference_name",
    "Job Title": "job_title",
    "Role": "role",
    "Job Portal": "portal_name",
    "skills": "skills_raw",
    "Company": "company_name",
    "Company Profile": "company_profile_raw",
}

REQUIRED_COLUMNS = ["job_id", "posting_date", "job_title", "company_name", "city", "country"]
INVALID_CITY_VALUES = {"Male", "Female", "Both"}


def parse_job_id(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(Decimal(text))
    except (InvalidOperation, ValueError):
        return None


def parse_company_profile(value):
    if pd.isna(value):
        return {}
    text = str(value).strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # The source dataset often stores pseudo-JSON with single quotes.
        safe_text = text.replace("'", '"')
        try:
            return json.loads(safe_text)
        except json.JSONDecodeError:
            return {}


def parse_posting_date(value):
    if pd.isna(value):
        return None
    if hasattr(value, "date"):
        try:
            return value.date()
        except (TypeError, ValueError):
            pass

    text = str(value).strip()
    if not text:
        return None

    if re.fullmatch(r"\d+(\.\d+)?", text):
        serial = float(text)
        # Excel date serial where day 1 is 1899-12-31 with leap-year offset.
        base = datetime(1899, 12, 30)
        try:
            return (base + timedelta(days=serial)).date()
        except OverflowError:
            return None

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def normalize_token_list(value):
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text:
        return None
    text = re.sub(r"[\{\}]", "", text)
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r",|(?<!\w)/(?!\w)|(?<=\))\s+|(?<=[a-zA-Z])\s{2,}", text)
    tokens = []
    seen = set()
    for part in parts:
        token = part.strip().strip("'\"")
        if not token:
            continue
        if token.lower() in seen:
            continue
        seen.add(token.lower())
        tokens.append(token)
    return " | ".join(tokens) if tokens else None


def parse_experience_range(value):
    if pd.isna(value):
        return (None, None)
    text = str(value).strip()
    if not text:
        return (None, None)
    nums = re.findall(r"\d+", text)
    if not nums:
        return (None, None)
    if len(nums) == 1:
        val = int(nums[0])
        return (val, val)
    return (int(nums[0]), int(nums[1]))


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(columns=RENAME_MAP)

    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace({"": None, "nan": None, "None": None})

    df["job_id"] = df["job_id_raw"].apply(parse_job_id)
    df["posting_date"] = df["posting_date_raw"].apply(parse_posting_date)
    df["min_salary"] = pd.to_numeric(df["min_salary_raw"], errors="coerce")
    df["max_salary"] = pd.to_numeric(df["max_salary_raw"], errors="coerce")
    df["latitude"] = pd.to_numeric(df["latitude_raw"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude_raw"], errors="coerce")

    exp_ranges = df["experience_raw"].apply(parse_experience_range)
    df["min_experience_years"] = exp_ranges.apply(lambda x: x[0])
    df["max_experience_years"] = exp_ranges.apply(lambda x: x[1])

    profiles = df["company_profile_raw"].apply(parse_company_profile)
    df["sector"] = profiles.apply(lambda x: x.get("Sector"))
    df["industry"] = profiles.apply(lambda x: x.get("Industry"))
    df["company_city"] = profiles.apply(lambda x: x.get("City"))
    df["company_state"] = profiles.apply(lambda x: x.get("State"))
    df["company_zip"] = profiles.apply(lambda x: x.get("Zip"))
    df["company_website"] = profiles.apply(lambda x: x.get("Website"))
    df["company_ticker"] = profiles.apply(lambda x: x.get("Ticker"))
    df["company_ceo"] = profiles.apply(lambda x: x.get("CEO"))

    df["skills_raw"] = df["skills_raw"].apply(normalize_token_list)
    benefits_series = df["Benefits"] if "Benefits" in df.columns else pd.Series([None] * len(df), index=df.index)
    df["benefits_raw"] = benefits_series.apply(normalize_token_list)

    df["portal_name"] = df["portal_name"].fillna("Unknown")
    df["preference_name"] = df["preference_name"].fillna("Unknown")

    for col in REQUIRED_COLUMNS:
        df = df[df[col].notna()]
    df = df[~df["city"].isin(INVALID_CITY_VALUES)]
    return df

