# region imports
from AlgorithmImports import *
import numpy as np
# endregion


#THE PURPOSE OF THIS ALGO IS TO ONLY FIND THE TOP AUTOCORRELATION STOCKS IN THE YEAR PRIOR
#MS, RY, BAC, AVGO, HD
class AdaptableGreenRhinoceros(QCAlgorithm):

    def initialize(self) -> None:
        #Time frame is 1 year before given period
        self.set_start_date(2023, 7, 1)
        self.set_end_date(2024, 7, 1)

        self.set_cash(1)
        self.done= False
        self.ret = []

        # Container that stores the current universe constituents
        self._active_symbols: Set[Symbol] = set()

        # stores prices for all univserse stocks in the given time period
        self.prices_map = {}

        self.universe_settings.resolution = Resolution.DAILY
        self.universe_settings.asynchronous = True
        self._universe = self.add_universe(self._fundamental_function)
    

    def on_securities_changed(self, changes: SecurityChanges) -> None:
        """Maintain the active symbol set when the universe changes."""
        for security in changes.added_securities:
            self._active_symbols.add(security.symbol)
        for security in changes.removed_securities:
            self._active_symbols.discard(security.symbol)

    #Initial Filter and add top 100 stocks by market cap
    def _fundamental_function(self, fundamental: list[Fundamental]) -> list[Symbol]: 
        #Only run once
        if not self.done:
            self.ret = []
            candidates = [c for c in fundamental if c.has_fundamental_data]

            #Initial filtering based off market cap
            #Cannot deal with all 8000 stocks
            candidates = sorted(candidates, key=lambda f: f.market_cap, reverse=True)[:100]
            candidates = [x.symbol for x in candidates]


            self.ret = candidates
            self.done = True
            self.debug([x.value for x in self.ret])
            self.debug(len(self.ret))

            for symbol in self.ret:
                self.add_equity(symbol.value, Resolution.DAILY)
                self.prices_map[symbol] = []

        return self.ret

    #Store prices for each candidate stock over time period
    def on_data(self, data: Slice):
        for symbol in list(self._active_symbols):
            if not data.contains_key(symbol) or not data[symbol]:
                continue

            price = data[symbol].close
            self.prices_map[symbol].append(price)

    #autocorrelation given prices
    def autocorr(self, prices):
        returns = np.diff(prices) / prices[:-1]
        autocorr = np.corrcoef(returns[1:], returns[:-1])[0, 1]
        return autocorr

    #using array of prices, calculate best 
    def OnEndOfAlgorithm(self) -> None:
        autocorr_map = {}

        for symbol in self.prices_map:
            prices = self.prices_map[symbol]
            auto = self.autocorr(prices)
            autocorr_map[symbol.value] = auto


        #Print best stocks
        sorted_stock_asc = sorted(autocorr_map.items(), key=lambda item: item[1])[-10:]
        for stock in sorted_stock_asc:
            self.debug([stock[0], stock]) 
