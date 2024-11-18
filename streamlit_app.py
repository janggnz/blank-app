import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Streamlit app
st.title('Huat Le Calculator')

# Sidebar inputs for ticker, data selector, moving averages, and horizontal lines
st.sidebar.header("Chart Configuration")

# User input for ticker in the sidebar
ticker = st.sidebar.text_input('Enter stock ticker (e.g., AAPL, MSFT, TSLA, ^DJI, ^GSPC, ^IXIC, )', '^DJI')

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

# Cache the data fetching function
@st.cache_data
def fetch_data(ticker, start, end):
    if start and end:
        # Fetch data based on the selected date range
        stock_data = yf.download(ticker, start=start, end=end)
    else:
        # Fetch all available data
        stock_data = yf.download(ticker)
    return stock_data

# 1-Month Chart
st.write("## 1-Month Chart")

# Fetch data for the last 1 month
one_month_start_date = datetime.today() - timedelta(days=30)
one_month_end_date = datetime.today()
one_month_data = fetch_data(ticker, one_month_start_date, one_month_end_date)

if not one_month_data.empty:
    # Prepare data for the 1-month candlestick chart
    dates = one_month_data.index
    open_prices = one_month_data['Open']
    high_prices = one_month_data['High']
    low_prices = one_month_data['Low']
    close_prices = one_month_data['Close']

    # Create candlestick chart using Plotly
    one_month_candlestick = go.Candlestick(x=dates,
                                           open=open_prices,
                                           high=high_prices,
                                           low=low_prices,
                                           close=close_prices)

    # Set layout for the 1-month chart
    one_month_layout = go.Layout(
        title=f'{ticker.upper()} 1-Month Candlestick Chart',
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        xaxis_rangeslider_visible=False
    )

    # Create the 1-month chart figure
    one_month_fig = go.Figure(data=[one_month_candlestick], layout=one_month_layout)

    # Display the 1-month chart
    st.plotly_chart(one_month_fig)

    # Find the extreme values (high and low) for the last month
    high_price = one_month_data['High'].max()  # Highest price in the last month
    low_price = one_month_data['Low'].min()    # Lowest price in the last month

    # Set pivot as the average of the high and low prices
    pivot_price = (high_price + low_price) / 2

    # Display the extreme values and pivot
    st.write(f"### Extreme Values for the Last Month:")
    st.write(f"High Price: {high_price:.3f}")
    st.write(f"Low Price: {low_price:.3f}")
else:
    st.error("No data available for the last 1 month.")


# Main Chart
st.write("## Main Chart")

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



# Fibonacci Calculator Section
st.write("## Fibo Calculator")

# Create three columns for the price inputs, pre-populated with the calculated high, low, and pivot values
col1, col2, col3 = st.columns(3)

# Input fields for Fibonacci calculations, aligned in a single row with specified initial values and allowing negatives
with col1:
    low_price_input = st.number_input("Low Price", value=low_price, format="%.3f")
with col2:
    high_price_input = st.number_input("High Price", value=high_price, format="%.3f")
with col3:
    pivot_price_input = st.number_input("Pivot Price", value=pivot_price, format="%.3f")

# Dropdowns for action (Buy/Sell) and computation method
col4, col5 = st.columns(2)

with col4:
    action = st.selectbox("Select Action", ["Buy", "Sell"], index=0)
with col5:
    fib_method = st.selectbox("Fibonacci Method", ["Retracement & Extension", "Price Projection & Expansion"])

# Refined Fibonacci calculations (as previously defined)
def compute_fibo_ret_ext(high, low, action):
    levels = {
        "RET 38%": 0.38196601125010515,
        "RET 50%": 0.5,
        "RET 62%": 0.6180339887498949,
        "RET 79%": 0.7861513777574233,
        "RET 89%": 0.886651779,
        "EXT 100%": 1,
        "EXT 112%": 1.127838485,
        "EXT 127%": 1.272019649514069,
        "EXT 162%": 1.6180339887498949,
        "EXT 262%": 2.6180339887498949,
    }
    fibonacci_results = {}
    for key, ratio in levels.items():
        if action == "Buy":
            if "RET" in key:  # Retracement logic for Buy
                fibonacci_results[key] = high - abs(high - low) * ratio
            elif "EXT" in key:  # Extension logic for Buy
                fibonacci_results[key] = high - abs(high - low) * ratio
        elif action == "Sell":
            if "RET" in key:  # Retracement logic for Sell
                fibonacci_results[key] = low + abs(high - low) * ratio
            elif "EXT" in key:  # Extension logic for Sell
                fibonacci_results[key] = low + abs(high - low) * ratio
    return fibonacci_results

# Refined Price Projection & Expansion function
def compute_fibo_pp_exp(high, low, pivot, action):
    levels = {
        "PP 62%": 0.6180339887498949,
        "PP 79%": 0.7861513777574233,
        "PP 89%": 0.886651779,
        "PP 100%": 1,
        "PP 112%": 1.127838485,
        "PP 127%": 1.272019649514069,
        "PP 162%": 1.6180339887498949,  # Added PP 162%
        "PP 262%": 2.6180339887498949,  # Added PP 262%
        "EXP 38%": 0.38196601125010515,
        "EXP 50%": 0.5,
        "EXP 62%": 0.6180339887498949,
        "EXP 100%": 1,
        "EXP 162%": 1.6180339887498949,
    }
    fibonacci_results = {}
    for key, ratio in levels.items():
        if action == "Buy":
            if "PP" in key:  # Price Projection logic for Buy (based on pivot)
                fibonacci_results[key] = pivot - abs(high - low) * ratio
            elif "EXP" in key:  # Expansion logic for Buy (based on low)
                fibonacci_results[key] = low - abs(high - low) * ratio
        elif action == "Sell":
            if "PP" in key:  # Price Projection logic for Sell (based on pivot)
                fibonacci_results[key] = pivot + abs(high - low) * ratio
            elif "EXP" in key:  # Expansion logic for Sell (based on high)
                fibonacci_results[key] = high + abs(high - low) * ratio
    return fibonacci_results

# Display Fibonacci results in two formats
if high_price_input > 0 and low_price_input > 0:
    if fib_method == "Retracement & Extension":
        # Compute Retracement & Extension levels
        fib_levels_result = compute_fibo_ret_ext(high_price_input, low_price_input, action)
    elif fib_method == "Price Projection & Expansion":
        # Compute Price Projection & Expansion levels
        fib_levels_result = compute_fibo_pp_exp(high_price_input, low_price_input, pivot_price_input, action)

st.write(f"### {fib_method}:")
# Create two columns side by side
col1, col2 = st.columns(2)

# Format 1: Display as a single line of values (only resultant values, with 3 decimal places) in the first column
with col1:
    st.write(f"### Single Line:")
    fib_values = ", ".join([f"{value:.3f}" for value in fib_levels_result.values()])  # Join values into a single string
    st.write(fib_values)  # Display the single line of values in the first column

# Format 2: Display as a table with explicit level labels in the second column
with col2:
    st.write(f"### Table:")
    fib_df = pd.DataFrame({
        "Level (%)": list(fib_levels_result.keys()),  # Fibonacci level labels (e.g., "RET 38%")
        "Price Levels": [f"{value:.3f}" for value in fib_levels_result.values()],  # Formatted price levels
    })
    st.dataframe(fib_df)  # Display the table in the second column
