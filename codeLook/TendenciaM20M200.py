import MetaTrader5 as mt5
import pandas_ta as ta

import pandas as pd
from datetime import datetime

import json 
from io import StringIO

with open("config.json") as json_data_file:
    data = json.load(json_data_file)
# Estabeleça conexão com o MetaTrader 5
mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password'])

# Defina o ticker da ação e o intervalo de tempo desejado
ticker = 'PETR4'
start_time = datetime(2020, 1, 1)
end_time = datetime(2023, 4, 30)

# Busque os dados históricos de preços da ação usando o MetaTrader 5
data = mt5.copy_rates_range(ticker, mt5.TIMEFRAME_D1, start_time, end_time)

# Converta os dados em um DataFrame do pandas e calcule as médias móveis e o ADX
df = pd.DataFrame(data)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)
df.ta.sma(length=20, append=True)
df.ta.sma(length=200, append=True)
df.ta.adx(append=True)

# print(df)

# Determine a tendência atual da ação
if df.iloc[-1]['close'] > df.iloc[-1]['SMA_20'] > df.iloc[-1]['SMA_200'] and \
   df.iloc[-1]['SMA_20'] > df.iloc[-20]['SMA_20'] and \
   df.iloc[-1]['SMA_200'] > df.iloc[-200]['SMA_200'] and \
   df.iloc[-1]['ADX_14'] > 25:
    print(f"A tendência de {ticker} é de alta.")
elif df.iloc[-1]['close'] < df.iloc[-1]['SMA_20'] < df.iloc[-1]['SMA_200'] and \
     df.iloc[-1]['SMA_20'] < df.iloc[-20]['SMA_20'] and \
     df.iloc[-1]['SMA_200'] < df.iloc[-200]['SMA_200'] and \
     df.iloc[-1]['ADX_14'] > 25:
    print(f"A tendência de {ticker} é de baixa.")
else:
    print(f"A tendência de {ticker} é indefinida.")
