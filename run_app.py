import time

from ibapi import contract

import ib_options_collector as col


underlying = contract.Contract()
underlying.conId = 756733
underlying.symbol = "SPY"
underlying.exchange = "SMART"
underlying.secType = "STK"
underlying.currency = "USD"

collector = col.ib_option_collector(underlying, 20180525)

time.sleep(2)
collector.disconnect_chain()
print('First chain done')

collector.change_subscription(20180601)
time.sleep(2)
print(collector.retrieve_option_chain())
