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
positions = {}  # To track holdings and reference prices
total_loss = {}  # To track total loss for each stock

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
            positions[symbol] = {'qty': 0, 'reference_price': 0}
            total_loss[symbol] = 0
        positions[symbol]['qty'] += qty
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

# Function to calculate total profit/loss
def calculate_pnl(symbol, current_price):
    if symbol in positions:
        reference_price = positions[symbol]['reference_price']
        qty = positions[symbol]['qty']
        return (current_price - reference_price) * qty
    return 0

# Main trading loop
while True:
    for stock in top_stocks:
        try:
            price = get_stock_price(stock)
            if price is None:
                print(f"Skipping {stock}: No trade data found")
                continue

            print(f"Current price of {stock}: ${price:.2f}")

            # Initialize reference price and total loss
            if stock not in positions:
                positions[stock] = {'qty': 0, 'reference_price': price}
                total_loss[stock] = 0

            # Calculate profit/loss
            pnl = calculate_pnl(stock, price)

            # Check profit to sell
            if pnl > 5:
                sell_stock(stock, positions[stock]['qty'])
                print(f"Sold all shares of {stock} for profit of ${pnl:.2f}")
                continue

            # Check loss to stop buying
            if pnl < -10 and total_loss[stock] <= 50:
                total_loss[stock] += abs(pnl)
                print(f"Total loss for {stock} is ${total_loss[stock]:.2f}, pausing buys.")
                continue

            # Stop completely if loss exceeds $100
            if total_loss[stock] > 100:
                print(f"Total loss for {stock} exceeded $100. Stopping trading for {stock}.")
                top_stocks.remove(stock)
                continue

            # Buy 1 share every minute
            if pnl > -50:  # Resume if loss exceeds $50 but less than $100
                buy_stock(stock, 1)
                positions[stock]['reference_price'] = price  # Update reference price

        except Exception as e:
            print(f"Error processing {stock}: {e}")

    time.sleep(60)  # Wait 1 minute before next iteration
