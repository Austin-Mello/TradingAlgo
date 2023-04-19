#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 16 22:02:34 2023

@author: austinmello
"""

import alpaca_trade_api as tradeapi
from alpaca_trade_api import REST
import pandas as pd
import ta
from os.path import exists

def RsiAlgo(API_KEY, SECRET_KEY, BASE_URL):
    api = tradeapi.REST(API_KEY, SECRET_KEY, BASE_URL, api_version='v2')
    #Preston, see edge cases in main for how we want to order buy and sell
    RsiBuy(api)
    RsiSell(api)

def RsiBuy(api): 
    timeframe = "1D"
    start = "2023-03-13"
    end = "2023-04-13"
    
    # Get S&P500 stock symbols
    # Pulled from wikipedia
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    tickers = table[0].Symbol
    #tickers = ["AAPL", "F"]   
    
    #RSI info: period, minimum threshold, and storage dataframe.
    rsiPeriod = 14
    rsiThreshold = 32
    rsis = pd.DataFrame(index=tickers, columns=['rsi'])
    
    #Quantity of stocks to buy
    quantity = 1
    
    #Collect RSI's
    for ticker in tickers:
        #Pull stock information
        bars = api.get_bars(ticker, timeframe, start, end).df
        #Get RSI
        rsi = ta.momentum.rsi(bars.close, rsiPeriod)[-1]
        #Add to the df
        rsis.at[ticker] = rsi
    
    if exists('Portfolio.csv'):
        portfolio = pd.read_csv('Portfolio.csv', index_col=(0))
    else:
        portfolio = pd.DataFrame(index=tickers, columns=['Position', 'Timestamp'])
        portfolio.Position = 0
        portfolio.Timestamp = 0
            
    #Add RSI's above the threshold to the portfolio.
    for ticker in tickers:
        if rsis.at[ticker, 'rsi'] > rsiThreshold:
            print(f"{ticker} is above RSI threshold!")
            try:
                float(api.get_position(ticker).qty)
            except Exception as exception:
                if exception.__str__() == 'position does not exist':
                    print(f'Buying {quantity} shares of {ticker}.')
                    api.submit_order(symbol=ticker, qty=quantity, side='buy', type='market',
                                             time_in_force='gtc')
                    portfolio.at[ticker, 'Timestamp'] = pd.Timestamp.now(tz='America/New_York')
                    portfolio.at[ticker, 'Position'] = quantity

    portfolio.to_csv('Portfolio.csv')
    
def RsiSell(api):
    #Import the portfolio
    if exists('Portfolio.csv'):
        portfolio = pd.read_csv('Portfolio.csv', index_col=(0))
        portfolio['Timestamp'] = pd.to_datetime(portfolio['Timestamp'])
    else:
        print('ERROR: Portfolio does not exist')
        return
    
    #Check the time each asset has been in the portfolio, sell accordingly.
    for ticker in portfolio.index:
        if (pd.Timestamp.now(tz='America/New_York') - portfolio['Timestamp'][ticker]) > pd.Timedelta(days=40):
            api.submit_order(symbol=ticker, qty=1, side='sell', type='market', time_in_force='gtc')
            portfolio['Position'][ticker] = 0
            portfolio['Timestamp'][ticker] = 0
        
        #Left this in to manually sell all and empty the portfolio
        '''r.submit_order(symbol=ticker, qty=1, side='sell', type='market', time_in_force='gtc')
        portfolio['Position'][ticker] = 0
        portfolio['Timestamp'][ticker] = 0'''
            
    portfolio.to_csv('Portfolio.csv')

    