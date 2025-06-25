# Stock-Correlation-Heatmap

**Overview**

This Streamlit application provides an interactive tool to visualise the correlation between the daily returns of various stock tickers. Understanding stock correlation is a fundamental concept in finance, especially for portfolio diversification, as it helps identify how different assets move in relation to each other.


**Features**

Popular Ticker Selection: Easily select from a list of commonly traded stocks (e.g., AAPL, MSFT, GOOG).

Custom Ticker Input: Add any valid stock ticker symbols you wish to analyse.

Flexible Date Range: Define custom start and end dates for your analysis.

Auto-Adjusted Prices Option: Choose whether to use automatically adjusted closing prices for accurate return calculations.

Interactive Heatmap Visualisation: A clear and intuitive heatmap displays the correlation coefficients between selected stocks.

Downloadable Data: Export the calculated correlation matrix as a CSV file for further analysis.


**Technologies Used**:

This application is built using the following Python libraries:

Streamlit: For building interactive web applications with pure Python.

yfinance: To fetch historical market data from Yahoo! Finance.

Pandas: For data manipulation and analysis.

Seaborn: For creating visually appealing statistical graphics (the heatmap).

Matplotlib: For plotting and customising the heatmap.
