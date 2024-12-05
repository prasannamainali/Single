import streamlit as st
import alpaca_trade_api as tradeapi
import time

# Retrieve API keys from Streamlit secrets
API_KEY = st.secrets["alpaca"]["api_key"]
API_SECRET = st.secrets["alpaca"]["api_secret"]
BASE_URL = "https://paper-api.alpaca.markets"

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')


# List of 100 most popular stocks (example tickers)
top_stocks = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'INTC']

# To store positions for tracking
positions = {}

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
        positions[symbol] = {'qty': qty, 'buy_price': get_stock_price(symbol)}
    except Exception as e:
        print(f"Error buying {symbol}: {e}")

# Function to sell stock
def sell_stock(symbol, qty):
    try:
        api.submit_order(symbol=symbol, qty=qty, side='sell', type='market', time_in_force='gtc')
        print(f"Sold {qty} shares of {symbol}")
        positions[symbol]['qty'] -= qty
        if positions[symbol]['qty'] <= 0:
            del positions[symbol]
    except Exception as e:
        print(f"Error selling {symbol}: {e}")

# Main trading loop
while True:
    for stock in top_stocks[:]:  # Iterate over a copy of the list
        try:
            price = get_stock_price(stock)
            if price is None:
                print(f"Skipping {stock}: No trade data found")
                continue

            print(f"Current price of {stock}: ${price:.2f}")

            # Buy logic: Buy 2 shares first
            if stock not in positions:
                print(f"Buying 2 shares of {stock}")
                buy_stock(stock, 2)

            # Sell logic: Check current position and decide to sell if price gain is more than $5
            if stock in positions and price >= positions[stock]['buy_price'] + 5:
                print(f"Selling {positions[stock]['qty']} shares of {stock} for profit")
                sell_stock(stock, positions[stock]['qty'])

            # Buy more logic: If price drops by $20 or more from last buy price
            if stock in positions and price <= positions[stock]['buy_price'] - 20:
                print(f"Buying 2 more shares of {stock} as price dropped by $20")
                buy_stock(stock, 2)

        except Exception as e:
            print(f"Error processing {stock}: {e}")
    
    time.sleep(60)  # Wait 1 minute before the next check
