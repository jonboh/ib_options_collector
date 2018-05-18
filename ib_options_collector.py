import time
from threading import Thread

import numpy as np

import client_impl
import subscriber_impl
import wrapper_impl
from ibapi import contract


class ib_option_collector(object):
    def __init__(self, underlyin_contract: contract, expiration: int, sub_limit=90, sub_float=10, twsport=7496,
                 client_id=1):
        # CONTRACTS
        self.underlyingcontract = underlyin_contract
        self.under_price_ticker = 1000
        self.opt_gen_contract = contract.Contract()
        self.opt_gen_contract.symbol = self.underlyingcontract.symbol
        self.opt_gen_contract.lastTradeDateOrContractMonth = expiration
        self.opt_gen_contract.secType = "OPT"
        self.opt_gen_contract.exchange = "SMART"
        self.opt_gen_contract.currency = self.underlyingcontract.currency
        self.opt_gen_contract.multiplier = "100"

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
        client_thread = Thread(target=self.__client_runner, name='IB Client Runner')
        client_thread.start()
        while not self.clientObj.isConnected():
            time.sleep(1)
        print('CONNECTED')
        self.request_generic_info()
        self.request_chain_info()
        # Subscribe to Underlying Price Feed
        self.clientObj.reqMktData_cust(0, self.under_price_ticker, self.underlyingcontract, "225,456", False, False, [])
        print('waiting for underlying price')
        while np.isnan(self.clientObj.wrapper.price_table_get_indexed(self.under_price_ticker, 'Bid')) or \
                np.isnan(self.clientObj.wrapper.price_table_get_indexed(self.under_price_ticker, 'Ask')):
            time.sleep(3)
        print('underlying price in place')
        self.run_subscription()

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
            time.sleep(1)

    def __client_runner(self):
        self.clientObj.run()

    def __subscriber_runner(self):
        if self.subscriberObj.sub_exists:
            self.subscriberObj.run()
        else:
            print('No Subscription Configuration in the Subscriber Object')
            raise ValueError

    def change_subscription(self, expiration):
        # CONTRACTS
        self.opt_gen_contract = contract.Contract()
        self.opt_gen_contract.symbol = self.underlyingcontract.symbol
        self.opt_gen_contract.lastTradeDateOrContractMonth = expiration
        self.opt_gen_contract.secType = "OPT"
        self.opt_gen_contract.exchange = "SMART"
        self.opt_gen_contract.currency = self.underlyingcontract.currency
        self.opt_gen_contract.multiplier = "100"

        self.request_generic_info()
        self.request_chain_info()

        self.run_subscription()


    def run_subscription(self):
        self.subscriberObj.define_subscription(self.under_price_ticker, self.opt_gen_contract, [],
                                               self.wrapperObj.expiration_strikes, self.sub_float)
        self.subscription_thread = Thread(target=self.__subscriber_runner, name='Subscription Runner')
        self.subscription_thread.start()

    def clear_all_subscriptions(self):
        self.subscriberObj.exit_trigger = True  # The subscriber is the one charged with the cancelation of the subscriptions
        while self.subscriberObj.active:
            time.sleep(1)

    def retrieve_option_chain(self):
        return self.wrapperObj.price_table_get()

    def disconnect_chain(self):
        self.subscriberObj.exit_trigger = True
        while self.subscriberObj.active:
            time.sleep(0.5)
        a = 1

    def destroy(self):
        self.disconnect_chain()
        self.clientObj.disconnect()
        self.subscriberObj.exit_trigger = True
        while self.subscriberObj.active:
            time.sleep(0.5)