import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Streamlit app
st.title('Candlestick Chart with Fibonacci Calculations')

# Sidebar inputs for ticker, data selector, moving averages, and horizontal lines
st.sidebar.header("Chart Configuration")

# User input for ticker in the sidebar
ticker = st.sidebar.text_input('Enter stock ticker (e.g., AAPL, MSFT, TSLA)', 'AAPL')

# Selector: Option to choose between all data or date range
option = st.sidebar.radio("Select Data Range", ('All available data', 'Select a date range'))

# Date input if user selects 'Select a date range'
if option == 'Select a date range':
    start_date = st.sidebar.date_input('Start date', datetime(2020, 1, 1))
    end_date = st.sidebar.date_input('End date', datetime.today() - timedelta(days=1))
else:
    start_date = None
    end_date = None

# Input fields for custom moving average periods
sma_1 = st.sidebar.number_input('Enter the period for the first moving average (e.g., 20)', min_value=1, value=20)
sma_2 = st.sidebar.number_input('Enter the period for the second moving average (e.g., 50)', min_value=1, value=50)

# Input for horizontal line values (separated by commas)
horizontal_lines_input = st.sidebar.text_input('Enter horizontal line values (separate by commas)', '')

# Input for horizontal line colors (separated by commas)
horizontal_line_colors_input = st.sidebar.text_input('Enter horizontal line colors (separate by commas, e.g., #177e89, #084c61, #db3a34)', '')

# Fetch data from yfinance
def fetch_data(ticker, start, end):
    if start and end:
        # Fetch data based on the selected date range
        stock_data = yf.download(ticker, start=start, end=end)
    else:
        # Fetch all available data
        stock_data = yf.download(ticker)
    return stock_data

# Check if ticker input is valid
if ticker:
    try:
        # Fetch stock data
        stock_data = fetch_data(ticker, start_date, end_date)

        # Flatten multi-index columns if present
        if isinstance(stock_data.columns, pd.MultiIndex):
            stock_data.columns = stock_data.columns.get_level_values(0)

        # Ensure all required columns are present
        required_columns = ['Open', 'High', 'Low', 'Close']
        if all(col in stock_data.columns for col in required_columns):
            st.sidebar.write(f"Showing data for {ticker.upper()}")

            # Display the data types of the columns in the sidebar
            st.sidebar.write("Data Types of the Columns:")
            st.sidebar.write(stock_data.dtypes)

            # Ensure all required columns are numeric (float or int)
            for col in required_columns:
                if not pd.api.types.is_numeric_dtype(stock_data[col]):
                    st.sidebar.write(f"Column {col} contains non-numeric values. Converting to numeric...")
                    # Convert column to numeric, coerce errors to NaN
                    stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
                    st.sidebar.write(f"After conversion, NaN values in {col}: {stock_data[col].isna().sum()}")

            # Drop any rows with NaN values in required columns
            stock_data.dropna(subset=required_columns, inplace=True)
            st.sidebar.write(f"Data after dropping rows with NaN values:")
            st.sidebar.dataframe(stock_data.tail())

            # Calculate user-defined Moving Averages
            stock_data[f'SMA{sma_1}'] = stock_data['Close'].rolling(window=sma_1).mean()
            stock_data[f'SMA{sma_2}'] = stock_data['Close'].rolling(window=sma_2).mean()

            # Prepare data for Plotly candlestick chart
            dates = stock_data.index
            open_prices = stock_data['Open']
            high_prices = stock_data['High']
            low_prices = stock_data['Low']
            close_prices = stock_data['Close']
            sma_1_values = stock_data[f'SMA{sma_1}']
            sma_2_values = stock_data[f'SMA{sma_2}']

            # Create candlestick chart using Plotly
            candlestick = go.Candlestick(x=dates,
                                         open=open_prices,
                                         high=high_prices,
                                         low=low_prices,
                                         close=close_prices)

            # Create moving average lines
            sma_1_line = go.Scatter(
                x=dates, y=sma_1_values,
                mode='lines', name=f'{sma_1}-day SMA',
                line=dict(color='blue', width=2)
            )

            sma_2_line = go.Scatter(
                x=dates, y=sma_2_values,
                mode='lines', name=f'{sma_2}-day SMA',
                line=dict(color='orange', width=2)
            )

            # Parse the horizontal line values and colors from user input
            horizontal_lines = []
            if horizontal_lines_input:
                try:
                    horizontal_lines = [float(val.strip()) for val in horizontal_lines_input.split(',')]
                except ValueError:
                    st.error("Invalid input for horizontal line values. Please enter valid numbers separated by commas.")

            horizontal_colors = []
            if horizontal_line_colors_input:
                horizontal_colors = [val.strip() for val in horizontal_line_colors_input.split(',')]

            # Define default colors for cycling
            default_colors = ['#177e89', '#084c61', '#db3a34', '#ffc857', '#323031']

            # Cycle through default colors if user-defined colors are insufficient
            if len(horizontal_colors) != len(horizontal_lines):
                st.warning("The number of colors doesn't match the number of lines. Defaulting to the first 5 colors and cycling.")
                for i in range(len(horizontal_lines)):
                    if i >= len(horizontal_colors):
                        horizontal_colors.append(default_colors[i % len(default_colors)])

            # Create horizontal lines based on the parsed values and colors
            horizontal_lines_traces = []
            for idx, val in enumerate(horizontal_lines):
                color = horizontal_colors[idx]
                horizontal_lines_traces.append(
                    go.Scatter(
                        x=[dates[0], dates[-1]],  # Start and end dates for the horizontal line
                        y=[val, val],  # The value at which the line will be drawn
                        mode='lines',
                        name=f'Horizontal Line at {val}',
                        line=dict(color=color, dash='dash'),
                    )
                )

            # Set the layout for the chart
            layout = go.Layout(
                title=f'{ticker.upper()} Candlestick Chart with {sma_1}-day and {sma_2}-day Moving Averages',
                xaxis_title='Date',
                yaxis_title='Price (USD)',
                xaxis_rangeslider_visible=False
            )

            # Create the figure for the candlestick, moving averages, and horizontal lines
            fig = go.Figure(data=[candlestick, sma_1_line, sma_2_line] + horizontal_lines_traces, layout=layout)

            # Display the chart in Streamlit
            st.plotly_chart(fig)

        else:
            st.error(f"Data does not contain the necessary columns (Open, High, Low, Close) or is empty.")

    except Exception as e:
        st.error(f"Error fetching data for {ticker.upper()}: {str(e)}")

# Fibonacci section at the bottom
st.write("## Fibonacci Calculator")

# Input fields for Fibonacci calculations
high_price = st.number_input("High Price", min_value=0.0, format="%.2f", value=0.0)
low_price = st.number_input("Low Price", min_value=0.0, format="%.2f", value=0.0)
pivot_price = st.number_input("Pivot Price", min_value=0.0, format="%.2f", value=0.0)

# Buy or Sell selector
action = st.radio("Select Action", ['Buy', 'Sell'])

# Fibonacci computation method
fib_method = st.selectbox("Fibonacci Method", ['Retracement', 'Extension', 'Price Projection', 'Expansion'])

# Function to calculate Fibonacci levels
def compute_fibonacci_levels(high, low, method):
    fibonacci_levels = {}
    if method == "Retracement":
        levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        for level in levels:
            fibonacci_levels[f"{int(level * 100)}%"] = high - (high - low) * level
    elif method == "Extension":
        levels = [1.272, 1.618, 2.0, 2.618]
        for level in levels:
            fibonacci_levels[f"{int(level * 100)}%"] = high + (high - low) * level
    elif method == "Price Projection":
        levels = [1.618, 2.0, 2.618]
        for level in levels:
            fibonacci_levels[f"{int(level * 100)}%"] = low + (high - low) * level
    elif method == "Expansion":
        levels = [1.618, 2.618]
        for level in levels:
            fibonacci_levels[f"{int(level * 100)}%"] = high + (high - low) * level
    return fibonacci_levels

# Show Fibonacci levels
if high_price > 0 and low_price > 0:
    fib_levels = compute_fibonacci_levels(high_price, low_price, fib_method)
    st.write(f"### Fibonacci {fib_method} Levels:")
    for level, value in fib_levels.items():
        st.write(f"{level}: {value:.2f}")
