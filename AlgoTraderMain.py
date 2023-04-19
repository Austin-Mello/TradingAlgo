import pandas as pd
#import time
from Config import *
from AlgoTraderRSI import RsiAlgo



def main():
    # Set up trading loop
    while True:
        RsiAlgo(API_KEY, SECRET_KEY, BASE_URL)
        
        # Wait for next trading day
        clock = api.get_clock()
        next_open = clock.next_open
        current_time = clock.timestamp

        # Calculate time until the next market open and add a small buffer (e.g., 60 seconds)
        wait_time = (next_open - current_time).total_seconds() + 60

        # Sleep until the next trading day
        time.sleep(wait_time)
    
main()





#ToDo:

    #Think really, really hard about any edge cases we missed.
    
    #EDGE CASE: If a stock is above the RSI threshold the same day we sell it,
    #   do we want to buy it again?
    
    #EDGE CASE: If we're already holding an asset, do we want to buy it anyway?
    
#Next phase:
    #Create a trading loop with timed function calls to RSI module
    
#Completed:
    #Put the portfolio in another module and import
    #Put keys into a config module and import
    #Make API call to buy the stock 
    #Add a sell feature (this might be harder)
    #Export RSI algo to a different module (Complete)
