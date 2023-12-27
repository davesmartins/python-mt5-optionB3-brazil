import MetaTrader5 as mt5
import py_vollib.black_scholes.greeks.analytical as greeks
import time

import json 
from io import StringIO

with open("config.json") as json_data_file:
    data = json.load(json_data_file)
# Estabeleça conexão com o MetaTrader 5
mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password'])

# Defina o ticker do ativo subjacente e o número da série de opções desejada
symbol = 'PETRQ266'
# option_series = '' # 'N202205'

# Busque as informações da opção desejada
mt5.symbol_select(symbol,True)
time.sleep(0.1) 
option_info = mt5.symbol_info_tick(symbol) # PETRQ266
option_info_more =mt5.symbols_get( symbol )

# print(option_info)
print(option_info_more)


# (SymbolInfo(custom=False, chart_mode=1, select=True, visible=True, session_deals=0, session_buy_orders=0, session_sell_orders=0, volume=5700, volumehigh=806300, 
#             volumelow=100, time=1682702160, digits=2, spread=1, spread_float=True, ticks_bookdepth=10, trade_calc_mode=35, trade_mode=4, start_time=0, 
#             expiration_time=1684540799, trade_stops_level=0, trade_freeze_level=0, trade_exemode=3, swap_mode=0, swap_rollover3days=3, margin_hedged_use_leg=False, 
#             expiration_mode=15, filling_mode=3, order_mode=127, order_gtc_mode=0, option_mode=0, option_right=1, bid=0.13, bidhigh=0.26, bidlow=0.1, ask=0.14, 
#             askhigh=0.52, asklow=0.13, last=0.14, lasthigh=0.26, lastlow=0.13, volume_real=5700.0, volumehigh_real=806300.0, volumelow_real=100.0, option_strike=21.18, 
#             point=0.01, trade_tick_value=0.01, trade_tick_value_profit=0.01, trade_tick_value_loss=0.01, trade_tick_size=0.01, trade_contract_size=1.0, 
#             trade_accrued_interest=0.0, trade_face_value=0.0, trade_liquidity_rate=0.0, volume_min=100.0, volume_max=56020428.0, volume_step=100.0, volume_limit=0.0, 
#             swap_long=0.0, swap_short=0.0, margin_initial=0.0, margin_maintenance=0.0, session_volume=0.0, session_turnover=0.0, session_interest=0.0, 
#             session_buy_orders_volume=0.0, session_sell_orders_volume=0.0, session_open=0.0, session_close=0.0, session_aw=0.0, session_price_settlement=0.0, 
#             session_price_limit_min=0.0, session_price_limit_max=0.0, margin_hedged=0.0, price_change=0.0, price_volatility=0.0, price_theoretical=0.0, price_greeks_delta=0.0, 
#             price_greeks_theta=0.0, price_greeks_gamma=0.0, price_greeks_vega=0.0, price_greeks_rho=0.0, price_greeks_omega=0.0, price_sensitivity=0.0, basis='PETR4', 
#             category='', currency_base='BRL', currency_profit='BRL', currency_margin='BRL', bank='', description='PETRE   /EDRPN   21,18', exchange='', formula='', 
#             isin='BRPETR4Q0YD8', name='PETRQ266', page='', path='GTWVM_BOV1A\\PETRQ266'),)

option_type = 'put'  # ou 'call'
option_stk = option_info_more.option_strike
option_expiry = option_info_more.expiration_time

# # Busque as informações do ativo subjacente
# underlying_info = mt5.symbol_info(symbol)
# underlying_price = mt5.symbol_info_tick(symbol).bid

# # Calcule o delta da opção
days_to_expiry = (mt5.datetime.strptime(option_expiry, '%Y-%m-%d') - mt5.datetime.now()).days
time_to_expiry = days_to_expiry / 365.0
r = 0.06  # Taxa livre de risco (defina o valor correto para o seu caso)
sigma = 0.25  # Volatilidade implícita (defina o valor correto para o seu caso)
delta = greeks.delta(option_type, option_info_more.bid, option_strike, time_to_expiry, r, sigma)

# # Exiba o valor do delta
print(f"O delta da opção {symbol} {option_expiry} {option_type} {option_strike:.2f} é {delta:.2f}")

