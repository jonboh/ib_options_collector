import threading
import datetime
import time
import numpy as np
import pandas as pd

from ibapi.common import *
from ibapi.contract import ContractDetails
from ibapi.ticktype import *
from ibapi import wrapper


class EWrapper(wrapper.EWrapper):
    def __init__(self):
        super().__init__()
        self.lock = threading.RLock()
        self.available_strikes = []
        self.expiration_strikes = []
        self.available_expirations = []
        self.info_request_dict = {}
        self._price_table = pd.DataFrame({
            'reqId': [],
            'Contract': [],
            'Active': [],
            'Bid': [],
            'Ask': [],
            'Last': [],
            'BidVol': [],
            'AskVol': [],
            'Strike': [],
            'Right': [],
            'BidPriced': [],
            'AskPriced': [],
            'Expiration': [],
            'CashDiv': [],
            'RefreshDate': []}, index=[])  # TickerId is the index

    def price_table_get(self):
        with self.lock:
            return self._price_table

    def price_table_get_indexed(self, index, column):
        with self.lock:
            return self._price_table.loc[index, column]

    def price_table_set(self, index, column, value):
        with self.lock:
            self._price_table.loc[index, column] = value

    def price_table_ticker(self, reqId):
        with self.lock:
            tickerId_bool = self._price_table.reqId == reqId
            tickerId_index = tickerId_bool[tickerId_bool].index
            return tickerId_index

    def price_table_sort(self):
        with self.lock:
            self._price_table = self._price_table.sort_values(['Strike'], ascending='False')

    def wait_price_filling(self, tickers):
        allpriced = False
        while not allpriced:
            with self.lock:
                allpriced = (
                all(np.logical_not(self._price_table[self._price_table.loc[:, 'Active']].loc[tickers, 'BidPriced'])) and
                all(np.logical_not(self._price_table[self._price_table.loc[:, 'Active']].loc[tickers, 'AskPriced'])))
            time.sleep(1)  # Sleep to avoid unnecessarily locking the price_table
        return True

    def tickPrice(self, reqId: TickerId, tickType: TickType, price: float,
                  attrib: TickAttrib):
        super().tickPrice(reqId, tickType, price, attrib)
        indexor = self.price_table_ticker(reqId)
        if tickType == 1:
            if price != -1:
                self.price_table_set(indexor, 'Bid', price)
            else:
                self.price_table_set(indexor, 'Bid', 0)
        elif tickType == 2:
            self.price_table_set(indexor, 'Ask', price)
        elif tickType == 4:
            self.price_table_set(indexor, 'Last', price)
        self.price_table_set(indexor, 'RefreshDate', datetime.datetime.now())

    def tickOptionComputation(self, reqId: TickerId, tickType: TickType,
                              impliedVol: float, delta: float, optPrice: float, pvDividend: float,
                              gamma: float, vega: float, theta: float, undPrice: float):

        super().tickOptionComputation(reqId, tickType, impliedVol, delta, optPrice, pvDividend, gamma, vega, theta,
                                      undPrice)
        indexor = self.price_table_ticker(reqId)
        if tickType == 10:
            self.price_table_set(indexor, 'BidVol', impliedVol)
        elif tickType == 11:
            self.price_table_set(indexor, 'AskVol', impliedVol)
        self.price_table_set(indexor, 'RefreshDate', datetime.datetime.now())
        self.price_table_set(indexor, 'CashDiv', pvDividend)

    def securityDefinitionOptionParameter(self, reqId: int, exchange: str,
                                          underlyingConId: int, tradingClass: str, multiplier: str,
                                          expirations: SetOfString, strikes: SetOfFloat):
        super().securityDefinitionOptionParameter(reqId, exchange, underlyingConId, tradingClass, multiplier,
                                                  expirations, strikes)
        if exchange == "SMART":
            print('RECEIVED OPTION CHAIN DETAILS')
            with self.lock:
                self.available_strikes = list(strikes)
                self.available_expirations.sort()
                self.available_expirations = list(expirations)
                self.available_expirations.sort()
            print('reqId: ', reqId, ' exchange ', exchange)

    def securityDefinitionOptionParameterEnd(self, reqId: int):
        super().securityDefinitionOptionParameterEnd(reqId)
        with self.lock:
            self.info_request_dict.update({reqId: True})
        print('reqId: ', reqId, ' finished -- [securityDefinitionOptionParameterEnd]')

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):
        super().contractDetails(reqId, contractDetails)
        with self.lock:
            self.expiration_strikes.append(contractDetails.summary.strike)

    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)
        with self.lock:
            unique_expiration_strikes = set(self.expiration_strikes)
            self.expiration_strikes = list(unique_expiration_strikes)
            self.expiration_strikes.sort()
            self.info_request_dict.update({reqId: True})
        print('reqId: ', reqId, ' finished -- [contractDetailsEnd]')

    def error(self, reqId: TickerId, errorCode: int, errorString: str):
        # super().error(reqId, errorCode, errorString)
        print("Error. Id: ", reqId, " Code: ", errorCode, " Msg: ", errorString)
        if errorCode == 300:
            print()

        if errorCode == 354:
            print()
