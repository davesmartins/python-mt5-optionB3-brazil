import MetaTrader5 as mt5
import py_vollib.black_scholes.implied_volatility as iv
import numpy as np

# Estabeleça conexão com o MetaTrader 5
mt5.initialize()

# Defina o ticker da ação e o intervalo de tempo desejado
ticker = 'PETR4'
start_date = '2020-01-01'
end_date = '2022-04-29'

# Baixe os dados históricos de preços da ação usando o MetaTrader 5
data = mt5.copy_rates_range(ticker, mt5.TIMEFRAME_D1, 
                             mt5.datetime(2022, 4, 29), 
                             mt5.datetime(2020, 1, 1))

# Converta os dados em um DataFrame do pandas
data = pd.DataFrame(data)
data['time'] = pd.to_datetime(data['time'], unit='s')
data.set_index('time', inplace=True)

# Calcule o preço atual da ação
current_price = data['close'][0]

# Baixe os dados de opções da ação usando o MetaTrader 5
options = mt5.symbol_info_tick(ticker).option

# Crie uma matriz para armazenar os preços das opções
option_prices = np.zeros(len(options))

# Baixe os preços de todas as opções disponíveis
for i in range(len(options)):
    option = mt5.symbol_info_tick(options[i])
    option_prices[i] = option.ask

# Calcule o IV atual da ação
current_iv = iv.implied_volatility(option_prices.mean(), current_price, current_price, 
                                   (mt5.datetime.now() - data.index[0]).days / 365, 0, 'c')

# Calcule o IV histórico da ação
historical_iv = iv.implied_volatility(option_prices, current_price, current_price, 
                                      (mt5.datetime.now() - data.index[0]).days / 365, 0, 'c')
historical_iv_mean = np.mean(historical_iv)
historical_iv_std = np.std(historical_iv)

# Calcule o IV Rank
iv_rank = (current_iv - historical_iv_mean) / historical_iv_std

# Exiba o IV Rank da ação
print(f"O IV Rank de {ticker} é {iv_rank}")

# Encerre a conexão com o MetaTrader 5
mt5.shutdown()
