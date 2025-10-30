# region imports
from AlgorithmImports import *
import numpy as np
import math
# endregion


#MAKE MONEY BASED OFF THE STOCKS FOUND IN THE PREVIOUS ALGORITHM
class AdaptableGreenRhinoceros(QCAlgorithm):

    def initialize(self) -> None:
        #2:1 train test split
        #Train
        self.set_start_date(2024, 7, 1)
        self.set_end_date(2025, 3, 1)

        #Test
        # self.set_start_date(2025, 3, 1)
        # self.set_end_date(2025, 7, 1)

        #store how many stocks are invested in every day for analysis
        self.num_invested = []

        self.set_cash(10000000)
        self.set_warm_up(5)

        # Add equities and store their symbols
        tickers: list[str] = ["RY", "HD", "MS", "AVGO", "BAC"]
        self._symbols: list[Symbol] = []
        for ticker in tickers:
            symbol: Symbol = self.add_equity(ticker, Resolution.DAILY).symbol
            self._symbols.append(symbol)

        #Store prices
        self.prices = {}
        for symbol in self._symbols:
            self.prices[symbol] = []



    def on_data(self, data: Slice) -> None:

        #store prices
        for symbol in self._symbols:
            if symbol not in data:
                continue
            price = data[symbol]
            if not price:
                continue
            price = price.close
            self.prices[symbol].append(price)

        #warmup
        if self.is_warming_up:
            return

        #store number of stocks invested today for logging
        numI = 0
        for symbol in self._symbols:
            if self.portfolio[symbol].invested:
                numI += 1

        self.num_invested.append(numI)

        #Act if a stock is to be bought or sold
        for symbol in self._symbols:
            vol, ret = self.weighted_volatility(self.prices[symbol])

            #Sell/Exit if return is below 0
            if self.portfolio[symbol].invested:
                if ret < 0 * vol:
                    self.set_holdings(symbol, 0)
                    # self.debug(f"RETURN {ret}, VOL {vol}, LIQUIDATE LONG")

            #Enter if return is > Z
            #Generally not all 5 stocks are simultaneously invested
            #Instead of 0.2, we can afford to give 0.33 to each
            #Minimize cash held and increase returns
            if ret > 0.9 * vol:
                if not self.portfolio[symbol].invested:
                    if ret > 0:
                        self.set_holdings(symbol, 0.4)
                        # self.debug(f"RETURN {ret}, VOL {vol}, BUY")
                        

    #Weighted volatility. Instead of using 1 window, we a short, medium, and long window
    #We weigh the volatility of stocks closer to the present more than volatility longer ago
    def weighted_volatility(self, prices):
        prices = prices[-20:]
        prices_array = np.array(prices)  # convert to NumPy array if not already
        log_returns = np.log(prices_array[1:] / prices_array[:-1])

        returns5day = pd.Series(log_returns[-5:])
        returns10day = pd.Series(log_returns[-10:])
        returns20day = pd.Series(log_returns[-19:])

        volatility5day = returns5day.std()
        volatility10day = returns10day.std()
        volatility20day = returns20day.std()

        #Average 5-day, 10-day, 20-day volatility
        volatility = (volatility5day + volatility10day + volatility20day)/3.0
        ret = (prices[-1] - prices[-2])/prices[-2]
        return volatility, ret


    #Log counts of how many invested
    def OnEndOfAlgorithm(self) -> None:
        self.debug("END")
        counts_map = {0:0, 1:0, 2:0, 3:0, 4:0, 5:0}
        for count in self.num_invested:
            counts_map[count] += 1
        for count in counts_map:
            self.debug(f"ON {counts_map[count]} DAYS, WE WERE INVESTED IN {count} STOCKS")
