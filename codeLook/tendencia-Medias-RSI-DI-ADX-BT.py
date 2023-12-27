import MetaTrader5 as mt5
import talib
import pandas as pd

# Estabeleça conexão com o MetaTrader 5
mt5.initialize()

# Defina o ticker da ação e o intervalo de tempo desejado
symbol = 'PETR4'
timeframe = mt5.TIMEFRAME_D1
start_date = '2019-01-01'
end_date = '2022-04-29'

# Baixe os dados históricos de preços da ação usando o MetaTrader 5
data = mt5.copy_rates_range(symbol, timeframe, mt5.datetime(2022, 4, 29), mt5.datetime(2019, 1, 1))

# Converta os dados em um DataFrame do pandas
data = pd.DataFrame(data)
data['time'] = pd.to_datetime(data['time'], unit='s')
data.set_index('time', inplace=True)

# Calcule a média móvel de 20 dias
data['SMA20'] = talib.SMA(data['close'], timeperiod=20)

# Calcule a média móvel de 200 dias
data['SMA200'] = talib.SMA(data['close'], timeperiod=200)

# Calcule o RSI
data['RSI'] = talib.RSI(data['close'], timeperiod=14)

# Calcule o ADX, DI- e DI+
data['ADX'] = talib.ADX(data['high'], data['low'], data['close'], timeperiod=14)
data['DI-'] = talib.MINUS_DI(data['high'], data['low'], data['close'], timeperiod=14)
data['DI+'] = talib.PLUS_DI(data['high'], data['low'], data['close'], timeperiod=14)

# Crie um DataFrame vazio para armazenar os sinais de tendência
trend_signals = pd.DataFrame(index=data.index)

# Identifique as tendências de alta e baixa
trend_signals['Tendência'] = None
trend_signals.loc[data['SMA20'] > data['SMA200'], 'Tendência'] = 'Alta'
trend_signals.loc[data['SMA20'] < data['SMA200'], 'Tendência'] = 'Baixa'

# Identifique as tendências de sobrecompra e sobrevenda
trend_signals['Sobrecompra/Sobrevenda'] = None
trend_signals.loc[data['RSI'] > 70, 'Sobrecompra/Sobrevenda'] = 'Sobrecomprado'
trend_signals.loc[data['RSI'] < 30, 'Sobrecompra/Sobrevenda'] = 'Sobrevendido'

# Identifique as tendências de movimento direcional
trend_signals['Movimento Direcional'] = None
trend_signals.loc[(data['DI+'] > data['DI-']) & (data['ADX'] > 25), 'Movimento Direcional'] = 'Alta'
trend_signals.loc[(data['DI+'] < data['DI-']) & (data['ADX'] > 25), 'Movimento Direcional'] = 'Baixa'

# Calcule os retornos diários
data['Retorno Diário']
