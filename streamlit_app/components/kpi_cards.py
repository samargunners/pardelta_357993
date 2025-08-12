import streamlit as st
from utils.formatters import fmt_currency, fmt_int, fmt_pct

def _fmt(value, kind):
    if value is None:
        return "—"
    if kind == "currency":
        return fmt_currency(value)
    if kind == "int":
        return fmt_int(value)
    if kind == "pct":
        return fmt_pct(value)
    return str(value)

def kpi_row(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        with col:
            st.metric(label=item["label"], value=_fmt(item["value"], item.get("fmt")))