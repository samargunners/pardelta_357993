import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from settings import PC_NUMBER, DEFAULT_DATE_WINDOW_DAYS
from services.metrics import (
    get_topline,
    get_hourly_sales,
    get_waste_summary,
    get_labor_kpis,
)
from components.kpi_cards import kpi_row
from components.charts import line_chart

st.set_page_config(page_title=f"Store {PC_NUMBER} — KPIs", layout="wide")
st.title(f"🏪 Store {PC_NUMBER} — Key Metrics")

# --- Date controls ---
end = st.date_input("End date", value=date.today())
start = st.date_input(
    "Start date",
    value=date.today() - timedelta(days=DEFAULT_DATE_WINDOW_DAYS),
)

if start > end:
    st.error("Start date must be on or before end date.")
    st.stop()

# --- KPI strip ---
with st.spinner("Loading KPIs…"):
    tl = get_topline(PC_NUMBER, start, end)

kpi_row([
    {"label": "Sales ($)", "value": tl.get("sales", 0), "fmt": "currency"},
    {"label": "Checks", "value": tl.get("checks", 0), "fmt": "int"},
    {"label": "Avg Check ($)", "value": tl.get("avg_check", 0), "fmt": "currency"},
    {"label": "Donuts Sold", "value": tl.get("donut_units", 0), "fmt": "int"},
    {"label": "Waste %", "value": tl.get("waste_pct", None), "fmt": "pct"},
    {"label": "Labor %", "value": tl.get("labor_pct", None), "fmt": "pct"},
])

st.divider()

# --- Hourly sales chart (last day in range) ---
chart_day = end
st.subheader(f"Hourly Sales — {chart_day}")
with st.spinner("Loading hourly sales…"):
    hourly_df = get_hourly_sales(PC_NUMBER, chart_day)

if hourly_df is None or hourly_df.empty:
    st.info("No hourly sales available for the selected date.")
else:
    fig = line_chart(hourly_df, x="time", y="value", title="Hourly Sales ($)")
    st.plotly_chart(fig, use_container_width=True)

# --- Waste & Labor summaries ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Waste summary")
    waste_df = get_waste_summary(PC_NUMBER, start, end)
    if waste_df is None or waste_df.empty:
        st.caption("No waste data in this range.")
    else:
        st.dataframe(waste_df)

with col2:
    st.subheader("Labor KPIs")
    labor_df = get_labor_kpis(PC_NUMBER, start, end)
    if labor_df is None or labor_df.empty:
        st.caption("No labor data in this range.")
    else:
        st.dataframe(labor_df)

st.markdown(
    """
    <small>Data loads via Supabase using read-only keys from Streamlit secrets.\
     If you see 0s, check table names and RLS policies.</small>
    """,
    unsafe_allow_html=True,
)