# streamlit_app/services/metrics.py
from datetime import date
from typing import Optional, Callable, List

import pandas as pd
from . import supabase_client as db  # <-- module import to avoid circulars

T_SALES = "donut_sales_hourly"
T_LABOR = "actual_table_labor"
T_WASTE = "usage_overview"

def _between(q, col: str, start: date, end: date):
    return q.gte(col, str(start)).lte(col, str(end))

def _num(s: Optional[pd.Series]) -> pd.Series:
    if s is None:
        return pd.Series(dtype="float64")
    return pd.to_numeric(s, errors="coerce")

def get_topline(pc_number: str, start: date, end: date) -> dict:
    # --- Sales ---
    sales_df = db.fetch_df(
        T_SALES,
        select="value,quantity",
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    total_sales = float(_num(sales_df.get("value")).sum()) if not sales_df.empty else 0.0
    donut_units = int(_num(sales_df.get("quantity")).sum()) if not sales_df.empty else 0

    # --- Labor (checks, labor %) ---
    labor_df = db.fetch_df(
        T_LABOR,
        select="actual_labor,sales_value,check_count",
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    checks = int(_num(labor_df.get("check_count")).sum()) if not labor_df.empty else 0
    avg_check = (total_sales / checks) if checks else 0.0
    if not labor_df.empty:
        labor_sales = float(_num(labor_df.get("sales_value")).sum())
        labor_cost = float(_num(labor_df.get("actual_labor")).sum())
        labor_pct = (labor_cost / labor_sales) if labor_sales else None
    else:
        labor_pct = None

    # --- Waste % (use ratio over the period) ---
    waste_df = db.fetch_df(
        T_WASTE,
        select="waste_dollar",
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    if not waste_df.empty and total_sales:
        waste_dollar = float(_num(waste_df.get("waste_dollar")).sum())
        waste_pct = waste_dollar / total_sales
    else:
        waste_pct = None

    return {
        "sales": total_sales,
        "checks": checks,
        "avg_check": avg_check,
        "donut_units": donut_units,
        "waste_pct": waste_pct,
        "labor_pct": labor_pct,
    }

def get_hourly_sales(pc_number: str, day: date) -> pd.DataFrame:
    df = db.fetch_df(
        T_SALES,
        select="time,value,quantity",
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: q.eq("date", str(day)),
        ],
    )
    if df.empty:
        return df
    df["value"] = _num(df["value"])
    df["quantity"] = _num(df["quantity"])
    out = (
        df.groupby("time", as_index=False)
        .agg({"value": "sum", "quantity": "sum"})
        .sort_values("time")
    )
    return out

def get_waste_summary(pc_number: str, start: date, end: date) -> pd.DataFrame:
    df = db.fetch_df(
        T_WASTE,
        select=(
            "date,ordered_qty,wasted_qty,waste_percent,waste_dollar,"
            "expected_consumption,product_type,pc_number,store_name"
        ),
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    return df

def get_labor_kpis(pc_number: str, start: date, end: date) -> pd.DataFrame:
    df = db.fetch_df(
        T_LABOR,
        select="date,actual_hours,actual_labor,sales_value,sales_per_labor_hour,check_count",
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    return df
