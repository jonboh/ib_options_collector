import time

from ibapi import contract

import options_collector as col

# MAKE SURE THE EXPIRATIONS ACTUALLY EXIST!

underlying = contract.Contract()
underlying.conId = 756733
underlying.symbol = "SPY"
underlying.exchange = "SMART"
underlying.secType = "STK"
underlying.currency = "USD"

collector = col.OptionsCollector()
collector.subscription(underlying, 20180720)

time.sleep(2)
collector.disconnect_subscription()
print('First chain done')

collector.subscription(underlying, 20180713)
time.sleep(2)
print(collector.retrieve_option_chain())
