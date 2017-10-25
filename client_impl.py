from ibapi.common import *
from ibapi.contract import Contract
from ibapi import client


class EClient(client.EClient):
    def __init__(self, wrapper):
        super().__init__(wrapper)
        self.reqId = 1

    def reqMktData_cust(self, reqId: TickerId, ticker_id, contract: Contract,
                        genericTickList: str, snapshot: bool, regulatorySnapshot: bool,
                        mktDataOptions: TagValueList):
        self.reqId = self.reqId + 1
        self.wrapper.price_table_set(ticker_id, 'reqId', self.reqId)
        self.wrapper.price_table_set(ticker_id, 'Contract',
                                     contract)  # Assign to the price_table the requested contract
        self.wrapper.price_table_set(ticker_id, 'Right', contract.right)
        self.wrapper.price_table_set(ticker_id, 'Expiration', contract.lastTradeDateOrContractMonth)
        self.wrapper.price_table_set(ticker_id, 'Strike', contract.strike)
        self.wrapper.price_table_set(ticker_id, 'Active', True)
        self.wrapper.price_table_set(ticker_id, 'BidPriced', False)
        self.wrapper.price_table_set(ticker_id, 'AskPriced', False)
        super().reqMktData(self.reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)

    def cancelMktData_cust(self, reqId: TickerId, ticker_id):
        self.wrapper.price_table_set(ticker_id, 'Active', False)
        self.wrapper.price_table_set(ticker_id, 'BidPriced', False)
        self.wrapper.price_table_set(ticker_id, 'AskPriced', False)
        reqId_c = int(self.wrapper.price_table_get_indexed(ticker_id, 'reqId'))
        super().cancelMktData(reqId_c)

    def reqContractDetails_cust(self, reqId: int, contract: Contract):
        self.reqId = self.reqId + 1
        super().reqContractDetails(self.reqId, contract)
        self.wrapper.info_request_dict.update({self.reqId: False})
        return self.reqId

    def reqSecDefOptParams_cust(self, reqId: int, underlyingSymbol: str,
                                futFopExchange: str, underlyingSecType: str,
                                underlyingConId: int):
        self.reqId = self.reqId + 1
        super().reqSecDefOptParams(self.reqId, underlyingSymbol, futFopExchange, underlyingSecType, underlyingConId)
        self.wrapper.info_request_dict.update({self.reqId: False})
        return self.reqId
