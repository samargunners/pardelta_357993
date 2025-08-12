def fmt_currency(x):
    try:
        return f"${x:,.0f}" if abs(x) >= 100 else f"${x:,.2f}"
    except Exception:
        return "—"

def fmt_int(x):
    try:
        return f"{int(round(float(x))):,}"
    except Exception:
        return "—"

def fmt_pct(x):
    try:
        return f"{x*100:.1f}%"
    except Exception:
        return "—"