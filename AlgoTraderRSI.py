#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 16 22:02:34 2023

@author: austinmello
"""

import alpaca_trade_api as tradeapi
from alpaca_trade_api import REST
import pandas as pd
import pandas_market_calendars as mcal
import ta
from os.path import exists
from datetime import datetime, timedelta
import pytz
import time

def RsiAlgo(api):
    RsiBuy(api)
    RsiSell(api)

def RsiBuy(api): 
    #Get the start and end dates for today and yesterday.
    today = datetime.now(pytz.timezone("US/Eastern"))
    nyse = mcal.get_calendar("NYSE")
    schedule = nyse.schedule(start_date=today - timedelta(days=40), end_date=today)
    market_dates = schedule.index.normalize()
    last_14_market_days = list(market_dates[-15:-1])
    Ylast_14_market_days = list(market_dates[-16:-2])
        
    start_date_iso = last_14_market_days[0].strftime('%Y-%m-%d')
    end_date_iso = last_14_market_days[-1].strftime('%Y-%m-%d')
    
    Ystart_date_iso = Ylast_14_market_days[0].strftime('%Y-%m-%d')
    Yend_date_iso = Ylast_14_market_days[-1].strftime('%Y-%m-%d')
        
    # Get S&P500 stock symbols
    # Pulled from wikipedia
    table = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    tickers = table[0].Symbol
    #tickers = ["AAPL", "F"]   
    
    #RSI info: period, minimum threshold, and storage dataframe.
    rsiPeriod = 15
    rsiThreshold = 32
    rsis = pd.DataFrame(index=tickers, columns=['rsi'])
    Yrsis = pd.DataFrame(index=tickers, columns=['rsi'])
    
    #Quantity of stocks to buy
    quantity = 1
    
    #Collect RSI's
    for ticker in tickers:
        #Pull stock information
        barset = api.get_bars(symbol=ticker, 
                              timeframe='1D',
                              start=start_date_iso, 
                              end=end_date_iso, 
                              limit=rsiPeriod)
        
        barsetPrices = pd.DataFrame([bar.c for bar in barset], columns=['c'])
        #Get RSI
        rsi = ta.momentum.rsi(barsetPrices.c, rsiPeriod - 1)[rsiPeriod - 2]
        
        #Add to the df
        rsis.at[ticker] = rsi
        
        #hold on half a sec
        print(f"pulling historical info on {ticker}. Give it half a sec")
        time.sleep(.5)
        
        #Pull yesterday's stock information
        barset = api.get_bars(symbol=ticker, 
                              timeframe='1D',
                              start=Ystart_date_iso, 
                              end=Yend_date_iso, 
                              limit=rsiPeriod)
        
        barsetPrices = pd.DataFrame([bar.c for bar in barset], columns=['c'])
        #Get RSI
        rsi = ta.momentum.rsi(barsetPrices.c, rsiPeriod - 1)[rsiPeriod - 2]
        #Add to the df
        Yrsis.at[ticker] = rsi
        
    #Import the porfolio.  If one doesn't exist, make one.
    if exists('Portfolio.csv'):
        portfolio = pd.read_csv('Portfolio.csv', index_col=(0))
    else:
        portfolio = pd.DataFrame(index=tickers, columns=['Position', 'Timestamp'])
        portfolio.Position = 0
        portfolio.Timestamp = 0
            
    #Add RSI's above the threshold to the portfolio.
    for ticker in tickers:
        if rsis.at[ticker, 'rsi'] > rsiThreshold and Yrsis.at[ticker, 'rsi'] <= rsiThreshold:
            print(f"{ticker} has passed the RSI threshold!")
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
        portfolio['Timestamp'] = pd.to_datetime(portfolio['Timestamp'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    else:
        print('ERROR: Portfolio does not exist')
        return
    
    print(portfolio)
    
    #Check the time each asset has been in the portfolio, sell accordingly.
    for ticker in portfolio.index:
        pd.Timestamp.now(tz='America/New_York') - portfolio['Timestamp'][ticker]
        if (pd.Timestamp.now(tz='America/New_York') - portfolio['Timestamp'][ticker]) > pd.Timedelta(days=40):
            print(f'Held {ticker} for 40 days. Selling off shares of {ticker}.')
            api.submit_order(symbol=ticker, qty=1, side='sell', type='market', time_in_force='gtc')
            portfolio.drop(value=ticker)
            portfolio['Position'][ticker] = 0
            portfolio['Timestamp'][ticker] = 0
        
        #Left this block in to manually sell all and empty the portfolio
        '''api.submit_order(symbol=ticker, qty=1, side='sell', type='market', time_in_force='gtc')
        #portfolio = portfolio.drop(ticker)
        print(f'deleted ticker {ticker}')
        #portfolio['Position'][ticker] = 0
        #portfolio['Timestamp'][ticker] = 0'''
            
    portfolio.to_csv('Portfolio.csv')

    