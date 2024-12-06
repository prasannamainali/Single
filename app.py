import alpaca_trade_api as tradeapi
import streamlit as st
import time

# Alpaca API keys (from Streamlit secrets)
API_KEY = st.secrets["alpaca"]["api_key"]
API_SECRET = st.secrets["alpaca"]["api_secret"]
BASE_URL = "https://paper-api.alpaca.markets"

# Initialize Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL)

# Expanded list of popular stocks
top_stocks = ['NVDA', 'TSLA', 'ETSY', 'AMD', 'META']
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

# Function to get account balance
def get_account_balance():
    try:
        account = api.get_account()
        return float(account.cash), float(account.portfolio_value)
    except Exception as e:
        print(f"Error fetching account balance: {e}")
        return 0, 0

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

# Function to calculate profit/loss for a stock
def calculate_stock_pnl(symbol):
    if symbol in positions:
        qty = positions[symbol]['qty']
        reference_price = positions[symbol]['reference_price']
        current_price = get_stock_price(symbol)
        if current_price:
            return (current_price - reference_price) * qty
    return 0

# Main trading loop
while True:
    cash, portfolio_value = get_account_balance()
    balance_usage = (portfolio_value - cash) / portfolio_value
    print(f"Cash: ${cash}, Portfolio Value: ${portfolio_value}, Balance Usage: {balance_usage:.2%}")

    if balance_usage <= 0.5:  # If balance usage is under 50%
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

                # Calculate individual stock profit/loss
                pnl = calculate_stock_pnl(stock)

                # Sell logic: If profit exceeds $5
                if pnl > 5:
                    sell_stock(stock, positions[stock]['qty'])
                    print(f"Sold all shares of {stock} for a profit of ${pnl:.2f}")
                    continue

                # Stop buying logic: If loss exceeds $10
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

    else:  # If balance usage exceeds 50%, monitor and sell for $20 profit per stock
        for stock, data in positions.items():
            pnl = calculate_stock_pnl(stock)
            if pnl > 20:
                sell_stock(stock, data['qty'])
                print(f"Sold all holdings of {stock} for individual profit of ${pnl:.2f}")

    time.sleep(60)  # Wait 1 minute before next iteration
