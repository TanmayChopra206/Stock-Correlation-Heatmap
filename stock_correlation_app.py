import streamlit as st
import yfinance as yf
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import date, timedelta
from io import StringIO

# Streamlit page setup
st.set_page_config(page_title="Stock Correlation Heatmap", layout="centered")

# --- Sidebar Configuration ---
st.sidebar.header("Settings")

# Select from popular tickers
st.sidebar.markdown("### 🔍 Choose Stock Tickers")
common_tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "NVDA", "META", "NFLX", "JPM", "XOM"]
selected_common = st.sidebar.multiselect(
    "Select from popular tickers:",
    options=common_tickers,
    default=common_tickers
)

# Custom ticker input
custom_input = st.sidebar.text_input(
    "Or enter custom tickers (comma-separated, e.g. BABA, SHOP, RBLX):",
    value=""
)
custom_tickers = [ticker.strip().upper() for ticker in custom_input.split(",") if ticker.strip()]
tickers = list(set(selected_common + custom_tickers))

# Date input
end_date = st.sidebar.date_input("End date:", value=date.today() - timedelta(days=1))
start_date = st.sidebar.date_input("Start date:", value=end_date - timedelta(days=100))

# Auto-adjust prices
auto_adjust = st.sidebar.checkbox("Use auto-adjusted prices", value=False)

# Spread tickers for ratio analysis
st.sidebar.markdown("### 📉 Spread Analysis (Price Ratio)")
spread_tickers = st.sidebar.multiselect(
    "Select exactly 2 tickers for ratio-based analysis:",
    options=tickers,
    default=tickers[:2] if len(tickers) >= 2 else []
)

# --- Main Title ---
st.title("📈 Stock Price Correlation Heatmap")
st.write("Analyse the correlation between daily returns of selected stocks.")

# --- Validation ---
if len(tickers) < 2:
    st.warning("Please select or enter at least two ticker symbols.")
    st.stop()

if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

# --- Data Fetching ---
@st.cache_data(show_spinner=True)
def get_data(tickers, start, end, auto_adjust):
    try:
        data = yf.download(tickers, start=start, end=end, auto_adjust=auto_adjust)
        if auto_adjust:
            price_data = data['Close']
        else:
            if 'Adj Close' not in data:
                raise ValueError("Missing 'Adj Close'. Try enabling auto-adjust.")
            price_data = data['Adj Close']
        return price_data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

with st.spinner("Downloading stock data..."):
    price_df = get_data(tickers, start_date, end_date, auto_adjust)

if price_df.empty:
    st.error("No data available. Try different tickers or a different date range.")
    st.stop()

# --- Correlation Calculation ---
returns = price_df.pct_change().dropna()
if returns.empty:
    st.error("Not enough data to calculate returns.")
    st.stop()

correlation_matrix = returns.corr()

# --- Heatmap Visualization ---
st.subheader("🔗 Correlation Matrix Heatmap")
fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(
    correlation_matrix,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    linewidths=0.5,
    cbar_kws={'label': 'Correlation Coefficient'},
    ax=ax
)
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.title(f"Correlation Matrix\n{start_date} to {end_date}")
st.pyplot(fig)

# --- Download Button ---
st.subheader("⬇️ Download Correlation Matrix")
csv_buffer = StringIO()
correlation_matrix.to_csv(csv_buffer)
st.download_button(
    label="Download CSV",
    data=csv_buffer.getvalue(),
    file_name="correlation_matrix.csv",
    mime="text/csv"
)

# --- Spread Analysis ---
if len(spread_tickers) == 2:
    st.subheader("📊 Spread Analysis: Price Ratio")

    ticker1, ticker2 = spread_tickers
    if ticker1 not in price_df.columns or ticker2 not in price_df.columns:
        st.warning("Selected tickers not found in data.")
    else:
        ratio_series = price_df[ticker1] / price_df[ticker2]
        avg_ratio = ratio_series.mean()
        std_ratio = ratio_series.std()
        latest_ratio = ratio_series.iloc[-1]

        st.write(f"**Latest Price Ratio ({ticker1}/{ticker2}):** {latest_ratio:.2f}")
        st.write(f"**Historical Average Ratio:** {avg_ratio:.2f}")

        if latest_ratio > avg_ratio:
            st.success("🔼 The current ratio is **above** the historical average.")
        else:
            st.info("🔽 The current ratio is **below** the historical average.")

        # Plot price ratio
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        ratio_series.plot(ax=ax2, label=f"{ticker1}/{ticker2}", color="purple")
        ax2.axhline(avg_ratio, color="gray", linestyle="--", label="Average Ratio")
        ax2.set_title(f"Price Ratio: {ticker1}/{ticker2}")
        ax2.set_ylabel("Ratio")
        ax2.legend()
        st.pyplot(fig2)

        # --- Z-Score Analysis ---
        z_score = (latest_ratio - avg_ratio) / std_ratio
        st.write(f"**Z-Score of Current Ratio:** {z_score:.2f}")

        if z_score > 2:
            st.warning("⚠️ Z-Score > 2: Ratio is significantly above the mean. Potential overbought.")
        elif z_score < -2:
            st.warning("⚠️ Z-Score < -2: Ratio is significantly below the mean. Potential oversold.")
        else:
            st.info("ℹ️ Z-Score is within normal range (-2 to 2).")

        # Plot z-score bands
        upper_band = avg_ratio + 2 * std_ratio
        lower_band = avg_ratio - 2 * std_ratio

        fig3, ax3 = plt.subplots(figsize=(10, 4))
        ratio_series.plot(ax=ax3, label=f"{ticker1}/{ticker2}", color="purple")
        ax3.axhline(avg_ratio, color="gray", linestyle="--", label="Mean")
        ax3.axhline(upper_band, color="red", linestyle="--", label="+2σ")
        ax3.axhline(lower_band, color="blue", linestyle="--", label="-2σ")
        ax3.set_title(f"Z-Score Analysis of {ticker1}/{ticker2} Ratio")
        ax3.set_ylabel("Ratio")
        ax3.legend()
        st.pyplot(fig3)

        # --- Signal Generation ---
        z_scores = (ratio_series - avg_ratio) / std_ratio
        signals = pd.Series("Hold", index=z_scores.index)
        signals[z_scores > 2] = "Short Spread"
        signals[z_scores < -2] = "Long Spread"
        signals[(z_scores > -1) & (z_scores < 1)] = "Exit"

        latest_signal = signals.iloc[-1]
        st.subheader("📍 Trade Signal")
        st.write(f"**Latest Signal ({z_scores.index[-1].date()}):** `{latest_signal}`")

        if latest_signal == "Short Spread":
            st.warning(f"📉 Suggestion: **Short {ticker1} / Long {ticker2}**")
        elif latest_signal == "Long Spread":
            st.success(f"📈 Suggestion: **Long {ticker1} / Short {ticker2}**")
        elif latest_signal == "Exit":
            st.info("🚪 Suggestion: **Exit Position / No Action**")

        # Plot z-score with thresholds
        fig4, ax4 = plt.subplots(figsize=(10, 4))
        z_scores.plot(ax=ax4, color="darkgreen", label="Z-Score")
        ax4.axhline(0, color="black", linestyle="--", lw=1)
        ax4.axhline(2, color="red", linestyle="--", lw=1, label="+2 Threshold")
        ax4.axhline(-2, color="blue", linestyle="--", lw=1, label="-2 Threshold")
        ax4.axhline(1, color="gray", linestyle="--", lw=0.5)
        ax4.axhline(-1, color="gray", linestyle="--", lw=0.5)
        ax4.set_title("Z-Score and Signal Thresholds")
        ax4.set_ylabel("Z-Score")
        ax4.legend()
        st.pyplot(fig4)

st.success("✅ Done! You can explore correlation, spread behavior, and trade signals.")
