import os
import time
from datetime import datetime
from tqdm import tqdm

import ccxt
import pandas as pd
import requests

import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, DateFormatter

from dotenv import load_dotenv

load_dotenv()

def query():

    binance_futures_tickers = requests.get(
        "https://fapi.binance.com/fapi/v1/ticker/24hr"
    ).json()
    binance_futures_tickers = [
        t
        for t in binance_futures_tickers
        if datetime.now().timestamp() - t["closeTime"] / 1000 < 86400 # cuz some alts delisted
    ]
    tickers = [t["symbol"] for t in binance_futures_tickers if t["symbol"].endswith("USDT")]
    print(f"no of tickers : {len(tickers)}")
    binance = ccxt.binance()
    binance.options["defaultType"] = "future"
    today_date = datetime.today().strftime("%Y-%m-%d")

    timeframe = "1d"  # <--------- Change this to get data for different timeframes

    # Use only if you have the same filepath
    if not os.path.exists(f"./data/{today_date}_{timeframe}"):
        os.makedirs(f"./data/{today_date}_{timeframe}")

        # # Inefficient way to get data but respects the rate limit in the event of other scripts running
    for ticker in tqdm(tickers):
        future = binance.fetch_ohlcv(ticker.replace("USDT", "/USDT"), timeframe, limit=5000)
        df = pd.DataFrame(future)
        df.set_index(0, inplace=True)
        df.columns = ["open", "high", "low", "close", "volume"]
        df.volume = df.volume * df.close
        df.index = pd.to_datetime(df.index, unit="ms")
        df.to_csv(f"./data/{today_date}_{timeframe}/{ticker.replace('USDT', '')}.csv")
        time.sleep(1.5)  # We are allowed 1200 requests per minute hence 1.25s

    # Create an empty list to store DataFrames
    dfs = []
    
    # Read all CSV files and store them in the list
    for ticker in tickers:
        file_path = f"./data/{today_date}_{timeframe}/{ticker.replace('USDT', '')}.csv"
        df = pd.read_csv(file_path, index_col=0)
        df = df[['close']]
        df.columns = [ticker]
        dfs.append(df)
    
    # Concatenate all DataFrames
    price_history = pd.concat(dfs, axis=1)
    
    # Convert index to datetime
    price_history.index = pd.to_datetime(price_history.index)
    
    # Sort the DataFrame by index
    price_history.sort_index(inplace=True)
    
    now = pd.Timestamp.now()
    one_year_ago = now - pd.DateOffset(years=1)
    price_history = price_history[price_history.index > one_year_ago]

    print(price_history.shape)

    return price_history, today_date, timeframe