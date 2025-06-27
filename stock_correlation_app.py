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

st.success("Done! You can interactively explore and download the results.")
