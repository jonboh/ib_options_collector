import time
import datetime
import os
import copy

from ibapi import contract

import options_collector as col

local_offset = time.timezone / 3600
cst_timezone = datetime.timezone(offset=datetime.timedelta(hours=-6 - local_offset), name='CST')
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
spx.exchange = "CBOE"
spx.secType = "IND"
spx.currency = "USD"

collector = col.OptionsCollector()
collector.request_contract_info(spy)
spy_contract_details = copy.deepcopy(collector.wrapperObj.last_contract_details)
collector.request_generic_info(spy)
spy_expirations = collector.wrapperObj.available_expirations
collector.request_contract_info(spx)
spx_contract_details = copy.deepcopy(collector.wrapperObj.last_contract_details)
spx_tradinghours = spx_contract_details.tradingHours
spx_cst_open = datetime.datetime(year=int(spx_tradinghours[0:4]), month=int(spx_tradinghours[4:6]),
                                 day=int(spx_tradinghours[6:8]),
                                 hour=int(spx_tradinghours[9:11]), minute=int(spx_tradinghours[11:13]),
                                 tzinfo=cst_timezone)
spx_cst_close = datetime.datetime(year=int(spx_tradinghours[14:18]), month=int(spx_tradinghours[18:20]),
                                  day=int(spx_tradinghours[20:22]),
                                  hour=int(spx_tradinghours[23:25]), minute=int(spx_tradinghours[25:27]),
                                  tzinfo=cst_timezone)
collector.request_generic_info(spx)
spx_expirations = collector.wrapperObj.available_expirations

if not os.path.isdir('SPY'):
    os.mkdir('SPY')
if not os.path.isdir('SPX'):
    os.mkdir('SPX')

while True:
    # SPY LOOP
    cst_time = datetime.datetime.now(tz=cst_timezone)
    if spx_cst_close > cst_time > spx_cst_open:
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
