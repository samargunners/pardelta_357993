from datetime import date
import pandas as pd

from services.supabase_client import fetch_df

# Table names (adjust if your schema differs)
T_SALES = "donut_sales_hourly"      # columns: pc_number, date, time, product_type, quantity, value, product_name
T_LABOR = "actual_table_labor"      # columns: pc_number, date, hour_range, actual_hours, actual_labor, sales_value, check_count, sales_per_labor_hour
T_WASTE = "usage_overview"          # columns: usage_id, date, ordered_qty, wasted_qty, waste_percent, waste_dollar, expected_consumption, product_type, pc_number, store_name


def _between(q, col, start, end):
    return q.gte(col, str(start)).lte(col, str(end))


def get_topline(pc_number: str, start: date, end: date) -> dict:
    # Sales totals
    sales_df = fetch_df(
        T_SALES,
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )

    total_sales = float(sales_df["value"].sum()) if "value" in sales_df else 0.0
    donut_units = int(sales_df["quantity"].sum()) if "quantity" in sales_df else 0
    # check_count is in actual_table_labor, not donut_sales_hourly
    labor_df = fetch_df(
        T_LABOR,
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    checks = int(labor_df["check_count"].sum()) if "check_count" in labor_df else 0
    avg_check = (total_sales / checks) if checks else 0.0

    # Waste % (usage_overview: wasted_qty, ordered_qty, waste_percent, waste_dollar)
    waste_df = fetch_df(
        T_WASTE,
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    if not waste_df.empty and "waste_percent" in waste_df.columns:
        waste_pct = float(waste_df["waste_percent"].mean())
    else:
        waste_pct = None

    # Labor % from actual_table_labor (sales_value, actual_labor)
    if not labor_df.empty and set(["actual_labor", "sales_value"]).issubset(labor_df.columns):
        labor_pct = (labor_df["actual_labor"].sum() / max(labor_df["sales_value"].sum(), 1))
    else:
        labor_pct = None

    return {
        "sales": total_sales,
        "checks": checks,
        "avg_check": avg_check,
        "donut_units": donut_units,
        "waste_pct": waste_pct,
        "labor_pct": labor_pct,
    }


def get_hourly_sales(pc_number: str, day: date) -> pd.DataFrame | None:
    df = fetch_df(
        T_SALES,
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: q.eq("date", str(day)),
        ],
    )
    if df.empty:
        return df
    # keep only the columns we need
    keep = [c for c in ["time", "product_type", "product_name", "value", "quantity"] if c in df.columns]
    df = df[keep].copy()
    if "time" in df.columns:
        df = df.sort_values("time")
    return df


def get_waste_summary(pc_number: str, start: date, end: date) -> pd.DataFrame | None:
    df = fetch_df(
        T_WASTE,
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    # Only keep relevant columns from usage_overview
    keep = [c for c in ["date", "ordered_qty", "wasted_qty", "waste_percent", "waste_dollar", "expected_consumption", "product_type", "pc_number", "store_name"] if c in df.columns]
    return df[keep] if not df.empty else df


def get_labor_kpis(pc_number: str, start: date, end: date) -> pd.DataFrame | None:
    df = fetch_df(
        T_LABOR,
        filters=[
            lambda q: q.eq("pc_number", pc_number),
            lambda q: _between(q, "date", start, end),
        ],
    )
    if df.empty:
        return df
    keep = [c for c in ["date", "actual_hours", "actual_labor", "sales_value", "sales_per_labor_hour"] if c in df.columns]
    return df[keep]