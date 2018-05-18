import time
from threading import Thread

import numpy as np

import client_impl
import subscriber_impl
import wrapper_impl
from ibapi import contract


class ib_option_collector(object):
    def __init__(self, sub_limit=90, sub_float=10, twsport=7496,
                 client_id=1):
        # CONNECTION SETTINGS
        self.subscription_limit = sub_limit
        self.sub_float = sub_float
        self.twsport = twsport
        self.client_number = client_id

        # Wrapper, Client and Subscriber Declaration.
        self.wrapperObj = wrapper_impl.EWrapper()
        self.clientObj = client_impl.EClient(self.wrapperObj)
        self.subscriberObj = subscriber_impl.optchain_subscriber(self.clientObj, self.subscription_limit)
        # Connection
        self.clientObj.connect("127.0.0.1", self.twsport, self.client_number)
        client_thread = Thread(target=self.clientObj.run, name='IB Client Runner')
        client_thread.start()
        while not self.clientObj.isConnected():
            time.sleep(1)
        print('CONNECTED')

    def request_generic_info(self):
        # Request Option Chain Details for Underlying
        info_req_id = self.clientObj.reqSecDefOptParams_cust(0, self.underlyingcontract.symbol, "",
                                                             self.underlyingcontract.secType,
                                                             self.underlyingcontract.conId)
        # Wait for the request to be filled
        while not self.wrapperObj.info_request_dict[info_req_id]:
            time.sleep(0.25)

    def request_chain_info(self):
        info_req_id = self.clientObj.reqContractDetails_cust(0, self.opt_gen_contract)
        # Wait for the request to be filled
        while not self.wrapperObj.info_request_dict[info_req_id]:
            time.sleep(0.25)

    def subscription(self,underlying_contract, expiration):
        # CONTRACTS
        self.underlyingcontract = underlying_contract
        self.under_price_ticker = 1000
        self.opt_gen_contract = contract.Contract()
        self.opt_gen_contract.symbol = self.underlyingcontract.symbol
        self.opt_gen_contract.lastTradeDateOrContractMonth = expiration
        self.opt_gen_contract.secType = "OPT"
        self.opt_gen_contract.exchange = "SMART"
        self.opt_gen_contract.currency = self.underlyingcontract.currency
        self.opt_gen_contract.multiplier = "100"

        # CONTRACTS
        self.opt_gen_contract = contract.Contract()
        self.opt_gen_contract.symbol = self.underlyingcontract.symbol
        self.opt_gen_contract.lastTradeDateOrContractMonth = expiration
        self.opt_gen_contract.secType = "OPT"
        self.opt_gen_contract.exchange = "SMART"
        self.opt_gen_contract.currency = self.underlyingcontract.currency
        self.opt_gen_contract.multiplier = "100"

        self.request_chain_info()
        self.request_generic_info()

        self._run_subscription()

    def _run_subscription(self):# Subscribe to Underlying Price Feed
        self.clientObj.reqMktData_cust(0, self.under_price_ticker, self.underlyingcontract, "225,456", False, False, [])
        print('waiting for underlying price')
        while np.isnan(self.clientObj.wrapper.price_table_get_indexed(self.under_price_ticker, 'Bid')) or \
                np.isnan(self.clientObj.wrapper.price_table_get_indexed(self.under_price_ticker, 'Ask')):
            time.sleep(0.25)
        print('underlying price in place')
        self.subscriberObj.define_subscription(self.under_price_ticker, self.opt_gen_contract, [],
                                               self.wrapperObj.expiration_strikes, self.sub_float)
        self.subscription_thread = Thread(target=self.subscriberObj.run, name='Subscription Runner')
        self.subscription_thread.start()

    def retrieve_option_chain(self):
        return self.wrapperObj.price_table_get()

    def disconnect_subscription(self):
        self.subscriberObj.unsub_underlying()
        self.subscriberObj.exit_trigger = True
        while self.subscriberObj.active:
            time.sleep(0.25)

    def destroy(self):
        self.disconnect_subscription()
        self.clientObj.disconnect()