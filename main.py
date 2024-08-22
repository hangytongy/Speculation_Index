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

from get_data import query
from telegram_push import send_photo_telegram

load_dotenv()

def calculate_speculation_index(df):
    # Calculate 90-day returns for all coins
    returns_90d = df.pct_change(periods=90)
    
    # Separate Bitcoin returns
    bitcoin_returns = returns_90d['BTCUSDT']
    altcoin_returns = returns_90d.drop('BTCUSDT', axis=1)
    
    # Compare each altcoin's return to Bitcoin's return
    outperforming = (altcoin_returns.T > bitcoin_returns).T
    
    # Calculate the percentage of altcoins outperforming Bitcoin
    speculation_index = outperforming.mean(axis=1) * 100
    
    # drop all zero values
    speculation_index = speculation_index[speculation_index != 0]
    return speculation_index

def main():
# Assuming 'df' is your dataframe with index as timestamp and columns as tickers
# For demonstration, let's create a sample dataframe
    df,today_date,timeframe = query()

    print(df.head())

    # Calculate the speculation index
    speculation_index = calculate_speculation_index(df)

    # Create the plot
    fig, ax1 = plt.subplots(figsize=(12,6))
    ax1.plot(speculation_index.index, speculation_index.values, color='#0086b3', linewidth=2)
    # Set the y-axis range
    ax1.set_ylim(0, 100)

    # Add labels and title
    ax1.set_title('Speculation Index', fontsize=16, fontweight='bold')
    ax1.set_xlabel('Year', fontsize=12)
    ax1.set_ylabel('Percentage', fontsize=12)

    # Add gridlines
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Add source attribution
    ax1.text(0.01, -0.15, 'source: salience', transform=plt.gca().transAxes, fontsize=8, alpha=0.7)

    if not os.path.exists(f"./spec_img"):
        os.makedirs(f"./spec_img")
    charts_file = os.path.join(os.getcwd()+'//spec_img', f"SpecIndex_{today_date}_{timeframe}.png")
    fig.savefig(charts_file)

    send_photo_telegram(charts_file,f"SpeculationIndex updated {today_date} Chart")