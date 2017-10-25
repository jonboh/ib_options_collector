import time
from threading import Thread

import numpy as np

import client_impl
import subscriber_impl
import wrapper_impl
from ibapi import contract


class ib_option_collector(object):
    def __init__(self, sub_limit=90, twsport=7496, client_id=1):
        self.twsport = twsport
        self.subscription_limit = sub_limit
        self.client_number = client_id
        self.under_price_ticker = 1000
        # Wrapper, Client and Subscriber Declaration.
        self.wrapperObj = wrapper_impl.EWrapper()
        self.clientObj = client_impl.EClient(self.wrapperObj)
        self.subscriberObj = subscriber_impl.optchain_subscriber(self.clientObj, self.subscription_limit)
        # Connection
        self.clientObj.connect("127.0.0.1", self.twsport, self.client_number)
        client_thread = Thread(target=self.__client_runner, name='IB Client Runner')
        client_thread.start()
        while not self.clientObj.isConnected():
            pass
        print('CONNECTED')

    def define_underlying(self, symbol="SPY", secType="STK", conId=756733, exchange="SMART"):
        # Underlying Declaration
        self.underlyingcontract = contract.Contract()
        self.underlyingcontract.symbol = symbol
        self.underlyingcontract.secType = secType
        self.underlyingcontract.conId = conId
        self.underlyingcontract.exchange = exchange

    def define_generic_option(self, expiration: int):
        self.opt_gen_contract = contract.Contract()
        self.opt_gen_contract.symbol = self.underlyingcontract.symbol
        self.opt_gen_contract.lastTradeDateOrContractMonth = expiration
        self.opt_gen_contract.secType = "OPT"
        self.opt_gen_contract.exchange = "SMART"
        self.opt_gen_contract.currency = "USD"
        self.opt_gen_contract.multiplier = "100"

    def request_generic_info(self):
        # Request Option Chain Details for Underlying
        info_req_id = self.clientObj.reqSecDefOptParams_cust(0, self.underlyingcontract.symbol, "",
                                                             self.underlyingcontract.secType,
                                                             self.underlyingcontract.conId)
        # Wait for the request to be filled
        while not self.wrapperObj.info_request_dict[info_req_id]:
            pass

    def request_chain_info(self):
        info_req_id = self.clientObj.reqContractDetails_cust(0, self.opt_gen_contract)
        # Wait for the request to be filled
        while not self.wrapperObj.info_request_dict[info_req_id]:
            pass

    def __client_runner(self):
        self.clientObj.run()

    def __subscriber_runner(self):
        if self.subscriberObj.sub_exists:
            self.subscriberObj.run()
        else:
            print('No Subscription Configuration in the Subscriber Object')
            raise exceptions.Error

    def run(self):
        # Subscribe to Underlying Price Feed
        self.clientObj.reqMktData_cust(0, self.under_price_ticker, self.underlyingcontract, "225", False, False, [])
        print('waiting for underlying price')
        while np.isnan(self.clientObj.wrapper.price_table_get_indexed(self.under_price_ticker, 'Bid')) or \
                np.isnan(self.clientObj.wrapper.price_table_get_indexed(self.under_price_ticker, 'Ask')):
            time.sleep(3)
        print('underlying price in place')
        # HERE WE NEED TO DECIDE THE WAY IN WHICH THE SUBSCRIPTION IS ORDERED, PERMANENT and FLOAT
        float_groups = 10
        self.subscriberObj.define_subscription(self.under_price_ticker, self.opt_gen_contract, [],
                                               self.wrapperObj.expiration_strikes, float_groups)
        self.subscription_thread = Thread(target=self.__subscriber_runner, name='Subscription Runner')
        self.subscription_thread.start()

    def clear_all_subscriptions(self):
        self.subscriberObj.exit_trigger = True  # The subscriber is the one charged with the cancelation of the subscriptions
        while self.subscriberObj.active:
            pass

    def default_execution(self, expiration):
        self.define_underlying()
        self.request_generic_info()
        print(self.clientObj.wrapper.available_expirations)
        self.define_generic_option(expiration=expiration)
        self.request_chain_info()
        self.run()
        time.sleep(30)
        self.wrapperObj.price_table_sort()
        print("Options Collector execution complete. Collection currently running...")
