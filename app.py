import streamlit as st
import yfinance as yf
import pandas as pd

# -------------------------
# PAGE SETUP
# -------------------------
st.set_page_config(page_title="Momentum Radar", layout="wide")


# -------------------------
# SIDEBAR CONTROLS
# -------------------------
st.sidebar.header("⚙️ Scan Settings")

MAX_PRICE = st.sidebar.slider("Max Stock Price ($)", 0.5, 20.0, 4.0, 0.5)

unlimited_price = st.sidebar.checkbox("No max price limit (scan all stocks)")

st.title(f"📈 Sub-${MAX_PRICE} Momentum Radar (Live)")

MIN_VOLUME = st.sidebar.number_input("Min Avg Volume", 10_000, 10_000_000, 100_000, step=50_000)



refresh_rate = st.sidebar.slider("Auto Refresh (seconds)", 5, 60, 15)

ticker_input = st.sidebar.text_area(
    "Tickers (comma separated)",
    "AAPL,TSLA,NVDA,SNDL,CENN,ZOM,MULN"
)

tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]


# -------------------------
# SCORING ENGINE
# -------------------------
def compute_score(df):
    close = df["Close"]

    recent_return = (close.iloc[-1] - close.iloc[0]) / close.iloc[0]
    momentum_score = max(0, min(40, recent_return * 200))

    avg_volume = df["Volume"].mean()
    volume_score = min(40, (avg_volume / 1_000_000) * 10)

    volatility = close.pct_change().std()
    stability_score = max(0, 20 - (volatility * 200))

    total = momentum_score + volume_score + stability_score

    return round(total, 2), round(momentum_score, 2), round(volume_score, 2), round(stability_score, 2)


# -------------------------
# SCANNER
# -------------------------
def scan_ticker(ticker):
    try:
        df = yf.Ticker(ticker).history(period="10d")

        if df is None or df.empty:
            return {
                "Ticker": ticker,
                "Status": "SKIP: DATA",
                "Price": 0,
                "Score": 0
            }

        price = float(df["Close"].iloc[-1])

        if price >= MAX_PRICE:
            return {
                "Ticker": ticker,
                "Status": "SKIP: PRICE",
                "Price": price,
                "Score": 0
            }

        avg_volume = df["Volume"].mean()
        if avg_volume < MIN_VOLUME:
            return {
                "Ticker": ticker,
                "Status": "SKIP: VOLUME",
                "Price": price,
                "Score": 0
            }

        score, mom, vol, stab = compute_score(df)

        return {
            "Ticker": ticker,
            "Status": "WATCH",
            "Price": price,
            "Score": score,
            "Momentum": mom,
            "VolumeScore": vol,
            "Stability": stab
        }

    except Exception as e:
        return {
            "Ticker": ticker,
            "Status": "ERROR",
            "Price": 0,
            "Score": 0,
            "Error": str(e)
        }


# -------------------------
# RUN SCAN BUTTON
# -------------------------
run = st.button("🔍 Run Scan")

if run:

    results = []

    for t in tickers:
        results.append(scan_ticker(t))

    df = pd.DataFrame(results)

    df = df.sort_values(by="Score", ascending=False)

    st.subheader("🔥 Ranked Results")

    st.dataframe(df, use_container_width=True)

    # Optional breakdown
    st.subheader("📊 Summary")
    st.write(df["Status"].value_counts())
