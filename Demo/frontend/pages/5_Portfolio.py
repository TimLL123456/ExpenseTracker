import streamlit as st
import pandas as pd

from datetime import date, datetime, timedelta
from lib.api import add_asset_transaction, get_asset_holdings, ApiError

import requests
from typing import Optional
import math


st.title("Expense Tracker")
st.header("Portfolio")


# -----------------------------
# Helpers (NaN-safe + formatting)
# -----------------------------
def clean_value(v):
    """Convert pandas NaN/NaT (and float nan) to None so JSON serialization won't fail."""
    if v is None:
        return None
    if pd.isna(v):
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def safe_float(v) -> Optional[float]:
    v = clean_value(v)
    if v is None:
        return None
    try:
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except Exception:
        return None


def safe_pct(numer: pd.Series, denom) -> pd.Series:
    """
    Safe percentage/division helper.

    - numer: pandas Series
    - denom: can be a scalar (float/numpy.float64) or a pandas Series
    """
    # Handle scalar NaN/inf/None
    if denom is None:
        return pd.Series([pd.NA] * len(numer), index=numer.index)

    if isinstance(denom, (int, float, bool)):
        try:
            d = float(denom)
            if math.isnan(d) or math.isinf(d) or d == 0:
                return pd.Series([pd.NA] * len(numer), index=numer.index)
            out = numer / d
            return out.replace([float("inf"), float("-inf")], pd.NA)
        except Exception:
            return pd.Series([pd.NA] * len(numer), index=numer.index)

    # Handle Series denom
    if isinstance(denom, pd.Series):
        denom_clean = denom.replace({0: pd.NA})
        out = numer / denom_clean
        return out.replace([float("inf"), float("-inf")], pd.NA)

    # Fallback
    try:
        d = float(denom)
        if d == 0 or math.isnan(d) or math.isinf(d):
            return pd.Series([pd.NA] * len(numer), index=numer.index)
        out = numer / d
        return out.replace([float("inf"), float("-inf")], pd.NA)
    except Exception:
        return pd.Series([pd.NA] * len(numer), index=numer.index)


# -----------------------------
# Pricing
# -----------------------------
@st.cache_data(ttl=300)
def get_current_price(asset_type: str, symbol: str) -> Optional[float]:
    try:
        if asset_type == "crypto":
            crypto_map = {
                "BTC": "bitcoin",
                "BNB": "binancecoin",
                "ADA": "cardano",
            }
            coin_id = crypto_map.get(symbol.upper(), symbol.lower())
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            data = r.json()
            return data.get(coin_id, {}).get("usd")

        elif asset_type == "stock":
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol.upper()}?range=1d&interval=1d"
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/91.0.4472.124 Safari/537.36"
                )
            }
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            return data["chart"]["result"][0]["meta"]["regularMarketPrice"]

    except Exception:
        return None


@st.cache_data(ttl=300)
def get_current_price_cached(asset_type: str, symbol: str) -> Optional[float]:
    return get_current_price(asset_type, symbol)


# -----------------------------
# UI Tabs
# -----------------------------
tab1, tab2, tab3 = st.tabs(["Add Manual", "Upload CSV/XLSX", "View Holdings"])


# -----------------------------
# Tab 1: Manual entry
# -----------------------------
with tab1:
    with st.form("add_entry"):
        asset_type = st.selectbox("Asset Type", options=["stock", "crypto"])
        symbol = st.text_input("Symbol", placeholder="e.g., AAPL or BTC")
        name = st.text_input("Name (optional)", placeholder="e.g., Apple Inc.")
        quantity = st.number_input("Quantity", min_value=0.0, step=0.01)
        price = st.number_input("Price", min_value=0.0, step=0.01)
        action = st.selectbox("Action", options=["buy", "sell"])
        trans_date = st.date_input("Date", value=date.today())
        remarks = st.text_input("Remarks (optional)")
        submit = st.form_submit_button("Add Entry")

        if submit:
            if not symbol.strip():
                st.warning("Symbol required.")
            else:
                entry = {
                    "date": trans_date.strftime("%Y-%m-%d"),
                    "asset_type": asset_type,
                    "symbol": symbol.strip(),
                    "name": name.strip() or None,
                    "quantity": float(quantity),
                    "price": float(price),
                    "action": action,
                    "remarks": remarks.strip() or None,
                }

                try:
                    _ = add_asset_transaction(
                        entry=entry,
                        base_url=st.session_state.api_base_url,
                        timeout_sec=int(st.session_state.api_timeout_sec),
                    )
                    st.success("Entry added!")
                except ApiError as e:
                    st.error(f"Error: {e}")


# -----------------------------
# Tab 2: Upload CSV/XLSX (NaN-safe)
# -----------------------------
with tab2:
    uploaded_file = st.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])
    dry_run = st.checkbox("Dry-run (validate only, do not submit)", value=False)

    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        rename_map = {
            "Date": "date",
            "Asset Type": "asset_type",
            "Stock Code": "symbol",
            "Stock Name": "name",
            "Bid Price": "price",
            "Quantity": "quantity",
            "Buy / Sell": "action",
            "Remarks": "remarks",
        }
        df = df.rename(columns=rename_map)

        expected_cols = ["date", "asset_type", "symbol", "price", "quantity", "action"]
        if not all(col in df.columns for col in expected_cols):
            st.error(f"File must have columns: {', '.join(expected_cols)} (name and remarks optional)")
        else:
            # Handle Excel numeric date serials
            if pd.api.types.is_numeric_dtype(df["date"]):
                df["date"] = df["date"].apply(
                    lambda x: (datetime(1900, 1, 1) + timedelta(days=x - 1)).strftime("%Y-%m-%d")
                )

            # Ensure date is always a string in YYYY-MM-DD format (invalid -> NaN)
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

            # Normalize text columns
            df["asset_type"] = df["asset_type"].astype(str).str.lower()
            df["action"] = df["action"].astype(str).str.lower()
            df["symbol"] = df["symbol"].astype(str).str.strip()

            if "Base Stock Price" in df.columns:
                df = df.drop("Base Stock Price", axis=1)

            # Coerce numeric columns; invalid -> NaN
            df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
            df["price"] = pd.to_numeric(df["price"], errors="coerce")

            # Validate rows
            def validate_row(r) -> Optional[str]:
                if clean_value(r["date"]) is None:
                    return "Invalid date"
                if clean_value(r["asset_type"]) not in ("stock", "crypto"):
                    return "asset_type must be stock/crypto"
                if clean_value(r["symbol"]) is None or str(r["symbol"]).strip() == "":
                    return "Missing symbol"
                if clean_value(r["action"]) not in ("buy", "sell"):
                    return "action must be buy/sell"

                q = safe_float(r["quantity"])
                p = safe_float(r["price"])
                if q is None or q <= 0:
                    return "Invalid quantity"
                if p is None or p <= 0:
                    return "Invalid price"
                return None

            df["_error"] = df.apply(validate_row, axis=1)
            invalid = df[df["_error"].notna()].copy()
            valid = df[df["_error"].isna()].copy()

            st.subheader("Upload preview")
            st.dataframe(df.drop(columns=["_error"]), use_container_width=True)

            c1, c2 = st.columns(2)
            c1.metric("Valid rows", int(len(valid)))
            c2.metric("Invalid rows", int(len(invalid)))

            if len(invalid) > 0:
                st.error("Some rows are invalid; see details below.")
                st.dataframe(invalid[["date", "asset_type", "symbol", "price", "quantity", "action", "_error"]])

            if dry_run:
                st.info("Dry-run enabled: no rows will be submitted.")
            else:
                if st.button("Submit valid rows"):
                    success_count = 0
                    errors = []

                    progress = st.progress(0)
                    total = max(int(len(valid)), 1)

                    for i, (_, row) in enumerate(valid.iterrows(), start=1):
                        try:
                            entry = {
                                "date": clean_value(row["date"]),
                                "asset_type": clean_value(row["asset_type"]),
                                "symbol": clean_value(row["symbol"]),
                                "name": clean_value(row.get("name")),
                                "quantity": float(row["quantity"]),
                                "price": float(row["price"]),
                                "action": clean_value(row["action"]),
                                "remarks": clean_value(row.get("remarks")),
                            }

                            _ = add_asset_transaction(
                                entry=entry,
                                base_url=st.session_state.api_base_url,
                                timeout_sec=int(st.session_state.api_timeout_sec),
                            )
                            success_count += 1

                        except Exception as e:
                            errors.append(f"Row {i}: {e}")

                        progress.progress(min(i / total, 1.0))

                    st.success(f"{success_count} entries added.")
                    if errors:
                        st.error("\n".join(errors))


# -----------------------------
# Tab 3: View Holdings + Charts
# -----------------------------
with tab3:
    filter_type = st.selectbox("Filter by Type", options=["All", "stock", "crypto"])
    fetch = st.button("Fetch Holdings")

    if fetch:
        try:
            asset_type = None if filter_type == "All" else filter_type

            data = get_asset_holdings(
                base_url=st.session_state.api_base_url,
                timeout_sec=int(st.session_state.api_timeout_sec),
                asset_type=asset_type,
            )

            if not data:
                st.info("No holdings found.")
            else:
                df = pd.DataFrame(data)

                # prices (cached)
                df["current_price"] = df.apply(
                    lambda r: get_current_price_cached(r["asset_type"], r["symbol"]),
                    axis=1,
                )

                # metrics
                df["current_value"] = df["net_quantity"] * df["current_price"]
                df["cost_basis"] = df["net_quantity"] * df["avg_buy_price"]
                df["gain_loss"] = df["current_value"] - df["cost_basis"]
                df["gain_loss_pct"] = safe_pct(df["gain_loss"], df["cost_basis"])

                total_current_value = df["current_value"].sum(skipna=True)
                df["weight_pct"] = safe_pct(df["current_value"], total_current_value)

                # table
                st.subheader("Holdings")
                st.dataframe(
                    df[
                        [
                            "asset_type",
                            "symbol",
                            "name",
                            "net_quantity",
                            "avg_buy_price",
                            "current_price",
                            "cost_basis",
                            "current_value",
                            "gain_loss",
                            "gain_loss_pct",
                            "weight_pct",
                        ]
                    ],
                    use_container_width=True,
                )

                # totals
                total_cost = df["cost_basis"].sum(skipna=True)
                total_current = df["current_value"].sum(skipna=True)
                total_gain = df["gain_loss"].sum(skipna=True)

                c1, c2, c3 = st.columns(3)
                c1.metric("Total Cost Basis", f"{total_cost:,.2f}")
                c2.metric("Total Current Value", f"{total_current:,.2f}")
                c3.metric("Total Gain/Loss", f"{total_gain:,.2f}")

                # download
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download holdings CSV",
                    data=csv_bytes,
                    file_name="holdings.csv",
                    mime="text/csv",
                )

                # -----------------------------
                # Charts
                # -----------------------------
                st.subheader("Charts")

                # 1) Allocation by symbol (current value)
                alloc_symbol = (
                    df[["symbol", "current_value"]]
                    .dropna()
                    .groupby("symbol", as_index=True)["current_value"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.caption("Allocation by symbol (Current Value)")
                st.bar_chart(alloc_symbol)

                # 2) Allocation by asset type (current value)
                alloc_type = (
                    df[["asset_type", "current_value"]]
                    .dropna()
                    .groupby("asset_type", as_index=True)["current_value"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.caption("Allocation by asset type (Current Value)")
                st.bar_chart(alloc_type)

                # 3) Gain/Loss by symbol
                pnl_symbol = (
                    df[["symbol", "gain_loss"]]
                    .dropna()
                    .groupby("symbol", as_index=True)["gain_loss"]
                    .sum()
                    .sort_values(ascending=False)
                )
                st.caption("Unrealized Gain/Loss by symbol")
                st.bar_chart(pnl_symbol)

                # 4) Scatter: cost basis vs current value
                scatter_df = df[["symbol", "cost_basis", "current_value"]].copy()
                scatter_df = scatter_df.dropna(subset=["cost_basis", "current_value"])
                scatter_df = scatter_df.rename(
                    columns={"cost_basis": "Cost Basis", "current_value": "Current Value"}
                )
                st.caption("Cost Basis vs Current Value (each point is a holding row)")
                st.scatter_chart(scatter_df, x="Cost Basis", y="Current Value")

                # 5) Top-N weights chart
                top_n = st.slider("Top N positions (by weight)", min_value=3, max_value=30, value=10)
                topw = (
                    df[["symbol", "current_value"]]
                    .dropna()
                    .groupby("symbol", as_index=False)["current_value"]
                    .sum()
                    .sort_values("current_value", ascending=False)
                    .head(top_n)
                )
                if not topw.empty:
                    denom = topw["current_value"].sum()
                    topw["weight_pct"] = safe_pct(topw["current_value"], denom)
                    st.caption("Top positions by weight")
                    st.dataframe(topw, use_container_width=True)
                    st.bar_chart(topw.set_index("symbol")["weight_pct"])

        except ApiError as e:
            st.error(f"Error: {e}")