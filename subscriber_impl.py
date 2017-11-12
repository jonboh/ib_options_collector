import copy
import numpy as np
import time

from ibapi import contract

import client_impl


class optchain_subscriber(object):
    def __init__(self, client: client_impl.EClient, sub_limit):
        self.clientObj = client
        self.subscription_lim = sub_limit
        self.under_reqId = None
        self.gen_opt = contract.Contract()
        self.permanentsub = None
        self.permanentsub_id = None  # Permanent id go from 3000 on
        self.float_groups = None
        self.floatsub = None
        self.floatsub_id = None  # Float id go from 4000 on
        self.floatsub_helper = None
        self.sub_exists = False
        self.exit_trigger = False
        self.active = False

    def define_subscription(self, underlying_reqId, generic_option: contract.Contract, permanent_subscription,
                            floating_subscription, float_groups):
        self.under_reqId = underlying_reqId
        self.gen_opt = generic_option
        self.permanentsub = permanent_subscription
        self.permanentsub_id = range(3000, 3000 + len(permanent_subscription))
        self.float_groups = float_groups
        self.floatsub = [list() for i in range(0, float_groups)]
        self.floatsub_id = [list() for i in range(0, float_groups)]
        self.floatsub_helper = [False for i in range(0, float_groups)]
        group_indexor = 0
        for i in range(0, len(floating_subscription)):
            self.floatsub[group_indexor].append(floating_subscription[i])
            self.floatsub_id[group_indexor].append(4000 + i)
            group_indexor = group_indexor + 1
            if group_indexor > float_groups - 1:
                group_indexor = 0
        self.sub_exists = True

    def run(self):
        self.active = True
        # Initialize permanent subscription
        self.subscribe_strikelist(self.permanentsub_id, self.permanentsub)
        # Start with the (last) group so that it can be properly canceled by the first one
        lenstrikes = len(self.permanentsub_id)
        maxlen_strike = 0
        for k in range(0, len(self.floatsub_id)):
            lenstrikes = lenstrikes + len(self.floatsub_id[k])
            if maxlen_strike < len(self.floatsub_id[k]):
                maxlen_strike = len(self.floatsub_id[k])
        excluded_groups = 0
        while lenstrikes - excluded_groups * maxlen_strike > self.subscription_lim:
            excluded_groups = excluded_groups + 1

        if lenstrikes > self.subscription_lim:
            print('ROTATING CHAIN SUBSCRIBED')
            concurrent_subs = -1
            for i in range(0, len(self.floatsub_id) - excluded_groups):
                if self.exit_trigger:
                    self.exit()
                concurrent_subs = concurrent_subs + 1
                self.floatsub_helper[i] = True
                self.subscribe_strikelist(self.floatsub_id[i], self.floatsub[i])
            self.clientObj.wrapper.wait_price_filling(self.floatsub_id[concurrent_subs])
            print('COMP SUB')
            for i in range(concurrent_subs + 1, self.float_groups):
                if self.exit_trigger:
                    self.exit()
                self.floatsub_helper[i - concurrent_subs - 1] = False
                self.cancel_sub_strikelist(self.floatsub_id[
                                               i - concurrent_subs - 1])  # cancel previous sub group, not the entire float subscription
                self.floatsub_helper[i] = True
                self.subscribe_strikelist(self.floatsub_id[i], self.floatsub[i])  # subscribe new strikes
                self.clientObj.wrapper.wait_price_filling(self.floatsub_id[i])
            print('INTERNAL LOOP')
            # count = 0
            while not self.exit_trigger:
                for i in range(0, self.float_groups):  # loop around float subscriptions
                    # print('Count: ',count,' Float_Group: ',i)
                    # count = count + 1
                    price_table = copy.deepcopy(self.clientObj.wrapper.price_table_get())
                    # print('Active Total: ',np.sum(price_table.loc[:,'Active']))
                    self.floatsub_helper[i - concurrent_subs - 1] = False
                    self.cancel_sub_strikelist(self.floatsub_id[
                                                   i - concurrent_subs - 1])  # cancel previous sub group, not the entire float subscription
                    self.floatsub_helper[i] = True
                    self.subscribe_strikelist(self.floatsub_id[i], self.floatsub[i])  # subscribe new strikes
                    self.clientObj.wrapper.wait_price_filling(self.floatsub_id[i])
            self.exit()
        else:  # Less strikes than subscription_limit
            print('COMPLETE CHAIN SUBSCRIBED')
            self.subscribe_strikelist(self.permanentsub_id, self.permanentsub)
            for i in range(0, len(self.floatsub)):
                self.subscribe_strikelist(self.floatsub_id[i], self.floatsub[i])
            while not self.exit_trigger:
                time.sleep(0.5)  # just wait for the exit trigger
            self.exit()

    def exit(self):
        self.cancel_sub_strikelist(self.permanentsub_id)
        for i in range(0, self.float_groups):  # loop around float subscriptions
            self.cancel_sub_strikelist(self.floatsub_id[i])
        if np.all(np.logical_not(self.clientObj.wrapper.price_table_get().Active)):
            print('All Subscriptions Canceled')
        else:
            print('Not all subs canceled. ERROR')
        self.active = False

    def subscribe_strikelist(self, ticker_ids, strikes):
        underlying_price = (self.clientObj.wrapper.price_table_get_indexed(self.under_reqId, 'Bid') +
                            self.clientObj.wrapper.price_table_get_indexed(self.under_reqId, 'Ask')) / 2
        if not len(strikes) == 0:
            for i in range(0, len(ticker_ids)):
                sub_contract = copy.deepcopy(self.gen_opt)
                sub_contract.strike = strikes[i]
                if sub_contract.strike <= underlying_price:
                    sub_contract.right = 'P'
                else:
                    sub_contract.right = 'C'
                self.clientObj.reqMktData_cust(0, ticker_ids[i], sub_contract, '225', False, False, [])

    def cancel_sub_strikelist(self, ticker_ids):
        for i in range(0, len(ticker_ids)):
            if self.clientObj.wrapper.price_table_get_indexed(ticker_ids[i], 'Active'):
                self.clientObj.cancelMktData_cust(0, ticker_ids[i])
            else:
                # print("Cancel Sub SKIPPED")
                pass
