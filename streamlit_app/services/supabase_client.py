from functools import lru_cache
from typing import Optional

import pandas as pd
from supabase import create_client
import streamlit as st
import traceback


@lru_cache(maxsize=1)
def _client():
    """Create and cache a Supabase client. Raises a helpful RuntimeError if secrets are missing."""
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError(
            "Supabase credentials not found in Streamlit secrets. Add SUPABASE_URL and SUPABASE_KEY to .streamlit/secrets.toml"
        )
    return create_client(url, key)


def fetch_df(table: str, select: str = "*", filters: Optional[list] = None) -> pd.DataFrame:
    """Fetch data from Supabase and return a DataFrame.

    On any error, log the traceback to Streamlit and return an empty DataFrame so the app can continue.
    """
    try:
        supa = _client()
        query = supa.table(table).select(select)
        if filters:
            for f in filters:
                query = f(query)
        res = query.execute()
        data = res.data or []
        return pd.DataFrame(data)
    except Exception as e:  # pragma: no cover - runtime guard
        tb = traceback.format_exc()
        # Log to Streamlit so users see the error in the app
        try:
            st.error(f"Error querying Supabase table '{table}': {e}")
            st.text(tb)
        except Exception:
            # In case Streamlit isn't available in this context, fallback to print
            print(f"Error querying Supabase table '{table}': {e}")
            print(tb)
        return pd.DataFrame()