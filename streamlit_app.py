import pandas as pd
import streamlit as st
import yfinance as yf
from tqdm import tqdm
import time

# Load ticker list
stock_list = pd.read_csv("tickers.csv")
stock_list = stock_list.iloc[:-2]
tickers = list(stock_list.Symbol)

# Function to update the stock database
def update_database():
    last_date = pd.read_csv("stock_data/3IINFOLTD.csv").iloc[-1].Date[:10]
    for i in tqdm(tickers):
        try:
            try:
                hist = yf.Ticker(i+".NS").history(start=last_date).iloc[1:].reset_index()
            except:
                hist = yf.Ticker(i+"-SM"+".NS").history(start=last_date).iloc[1:].reset_index()
            data = pd.read_csv("stock_data/{}.csv".format(i))
            result = pd.concat([data, hist], ignore_index=True)
            result.to_csv("stock_data/{}.csv".format(i))
        except:
            print(i)

# Functions for pattern detection
def is_mostly_negatively_sloped(lst):
    negative_count = 0
    positive_count = 0
    
    if lst[0] < lst[-1]:
        return False
     
    for i in range(1, len(lst)): 
        if lst[i] < lst[i - 1]:
            negative_count += 1
        elif lst[i] > lst[i - 1]:
            positive_count += 1
    
    return negative_count > positive_count

def check_conditions_for_marubozu(open_price, high_price, low_price, close_price, tolerance_percent=0.05):
    open_tolerance = open_price * tolerance_percent / 100.0
    close_tolerance = close_price * tolerance_percent / 100.0
    
    condition1 = open_price < close_price
    condition2 = abs(high_price - close_price) <= close_tolerance
    condition3 = abs(open_price - low_price) <= open_tolerance
    
    return condition1 and condition2 and condition3

def check_conditions_for_hammer(open_price, high_price, low_price, close_price, tolerance_percent=0.05):
    open_tolerance = open_price * tolerance_percent / 100.0
    close_tolerance = close_price * tolerance_percent / 100.0
    
    condition1 = (min(close_price, open_price) - low_price) > 2*(abs(open_price - close_price))
    condition2 = abs(max(close_price, open_price)  - high_price) <= close_tolerance
    
    return condition1 and condition2

def calculate_ema(prices, span):
    prices_series = pd.Series(prices)
    ema = prices_series.ewm(span=span, adjust=False).mean()
    return list(ema)

def check_conditions_for_ema(close, short=9, long=21):
    close_short = calculate_ema(close, short)
    close_long = calculate_ema(close, long)
    
    if close_short[-3] < close_long[-3]:
        for i in range(1, 3):
            if close_short[-i] > close_long[-i]:
                return close_short, close_long
            
    return False

def get_bearish(tickers):
    final = []
    for i in tqdm(tickers):
        try:
            close = list(pd.read_csv("stock_data/"+i+".csv")[-20:].Close)
            if is_mostly_negatively_sloped(close):
                final.append(i)
        except:
            continue
    return final

def get_patterns(bearish):
    marubozu = []
    hammer = []
    ema = []
    for i in bearish:
        try:
            df = pd.read_csv("stock_data/"+i+".csv")[-2:]
            for j in range(2):
                open, high, low, close = df.iloc[j].Open, df.iloc[j].High, df.iloc[j].Low, df.iloc[j].Close
                if check_conditions_for_marubozu(open, high, low, close):
                    if i not in marubozu:
                        marubozu.append(i)
                if check_conditions_for_hammer(open, high, low, close):
                    if i not in hammer:
                        hammer.append(i)
            
            close = pd.read_csv("stock_data/"+i+".csv")[-50:].Close
            if check_conditions_for_ema(close):
                ema.append(i)
        except:
            continue
    return marubozu, hammer, ema

# Streamlit UI
def main():
    st.title("Stock Pattern Detection App")
    
    # Database update section
    if st.button("Update Database"):
        st.write("Updating database, please wait...")
        
        # Progress meter
        progress_bar = st.progress(0)
        total_tickers = len(tickers)
        
        for idx, ticker in enumerate(tickers):
            update_database()  # Call the actual update logic
            progress_bar.progress((idx + 1) / total_tickers)
        
        st.write("Database update completed!")
    
    # Pattern detection section
    st.write("Detect Bearish Stocks")
    
    if st.button("Detect Patterns"):
        bearish_stocks = get_bearish(tickers)
        st.write("Bearish Stocks:", bearish_stocks)
        
        marubozu, hammer, ema = get_patterns(bearish_stocks)
        
        st.write("Marubozu Pattern Detected in:", marubozu)
        st.write("Hammer Pattern Detected in:", hammer)
        st.write("EMA Crossover Detected in:", ema)

main()
