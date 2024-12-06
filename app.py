import alpaca_trade_api as tradeapi
import streamlit as st
import time

# Alpaca API keys (from Streamlit secrets)
API_KEY = st.secrets["alpaca"]["api_key"]
API_SECRET = st.secrets["alpaca"]["api_secret"]
BASE_URL = "https://paper-api.alpaca.markets"

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL)

# List of stocks to trade
top_stocks = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA']
positions = {}  # To track holdings

# Function to get the current stock price
def get_stock_price(symbol):
    try:
        barset = api.get_latest_trade(symbol)
        return barset.price
    except Exception as e:
        print(f"Error fetching price for {symbol}: {e}")
        return None

# Function to buy stock
def buy_stock(symbol, qty):
    try:
        api.submit_order(symbol=symbol, qty=qty, side='buy', type='market', time_in_force='gtc')
        print(f"Bought {qty} shares of {symbol}")
        if symbol not in positions:
            positions[symbol] = 0
        positions[symbol] += qty
    except Exception as e:
        print(f"Error buying {symbol}: {e}")

# Function to sell stock
def sell_stock(symbol, qty):
    try:
        api.submit_order(symbol=symbol, qty=qty, side='sell', type='market', time_in_force='gtc')
        print(f"Sold {qty} shares of {symbol}")
        positions[symbol] -= qty
        if positions[symbol] <= 0:
            del positions[symbol]
    except Exception as e:
        print(f"Error selling {symbol}: {e}")

# Main trading loop
while True:
    for stock in top_stocks:
        try:
            price = get_stock_price(stock)
            if price is None:
                print(f"Skipping {stock}: No trade data found")
                continue

            print(f"Current price of {stock}: ${price:.2f}")

            # If the stock is not in positions, decide to buy
            if stock not in positions:
                reference_price = price  # Reference price when considering buying
                drop_percentage = (reference_price - price) / reference_price
                if -0.75 < drop_percentage <= -0.005:  # Buy if within range
                    buy_stock(stock, 2)
                    positions[stock] = reference_price
                elif drop_percentage <= -0.75:  # Stop buying if too low
                    print(f"Stock {stock} is down more than 0.75%, stopping further buys.")
                    continue

            # If the stock is already in positions, check for selling conditions
            if stock in positions:
                reference_price = positions[stock]
                gain_percentage = (price - reference_price) / reference_price
                if gain_percentage >= 0.005:  # Sell if price increased by 0.5%
                    sell_stock(stock, positions[stock])
                elif (reference_price - price) / reference_price <= -0.75:  # Stop further actions if down > 0.75%
                    print(f"Stock {stock} is down more than 0.75%, holding position.")
                    continue

        except Exception as e:
            print(f"Error processing {stock}: {e}")

    time.sleep(60)  # Check every minute
