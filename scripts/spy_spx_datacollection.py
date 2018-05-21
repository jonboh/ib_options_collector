import time
import datetime
import os

from ibapi import contract

import options_collector as col

dateformat = "%Y%m%d%H%M%S"

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


if not os.path.isdir('SPY'):
    os.mkdir('SPY')
if not os.path.isdir('SPX'):
    os.mkdir('SPX')

while True:
    # SPY LOOP
    for expiration in spy_expirations:
        print('Collecting SPY ' + expiration)
        collector.subscription(spy, int(expiration))
        time.sleep(10)
        collector.retrieve_option_chain().to_csv(
            'SPY/' + 'SPY_' + expiration + '_' + datetime.datetime.now().strftime(dateformat) + '.csv')
        collector.disconnect_subscription()
    # SPX LOOP
    for expiration in spx_expirations:
        print('Collecting SPX ' + expiration)
        collector.subscription(spx, int(expiration))
        time.sleep(10)
        collector.retrieve_option_chain().to_csv(
            'SPX/' + 'SPX_' + expiration + '_' + datetime.datetime.now().strftime(dateformat) + '.csv')
        collector.disconnect_subscription()
