import time

from ibapi import contract

import options_collector as col

# info from: https://pennies.interactivebrokers.com/cstools/contract_info/

spy = contract.Contract()
spy.conId = 756733
spy.symbol = "SPY"
spy.exchange = "SMART"
spy.secType = "STK"
spy.currency = "USD"


spx = contract.Contract()
spx.conId = 416904
spx.symbol = "SPX"
spx.exchange = "SMART"
spx.secType = "IND"
spx.currency = "USD"


collector = col.OptionsCollector()
collector.request_generic_info(spy)
spy_expirations = collector.wrapperObj.available_expirations
collector.request_generic_info(spx)
spx_expirations = collector.wrapperObj.available_expirations
# SPY LOOP
while True:
    for expiration in spy_expirations:
        print('Collecting SPY ' + expiration)
        collector.subscription(spy, int(expiration))
        time.sleep(10)
        collector.disconnect_subscription()

    for expiration in spx_expirations:
        print('Collecting SPX ' + expiration)
        collector.subscription(spx, int(expiration))
        time.sleep(10)
        collector.disconnect_subscription()
