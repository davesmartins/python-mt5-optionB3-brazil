import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
from math import ceil
import yfinance as yf

# Função para calcular o preço teórico de uma opção usando o modelo de Black-Scholes
def black_scholes(S, K, T, r, option_type, sigma):
    d1 = (np.log(S/K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'C':
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'P':
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    return price

# Estabeleça conexão com o MetaTrader 5
mt5.initialize()

# Defina o ticker da ação e o intervalo de tempo desejado
ticker = 'PETR4'
start_time = datetime(2020, 1, 1)
end_time = datetime(2023, 4, 30)

# Defina o prazo de vencimento das opções
expiration_date = datetime(2023, 7, 21)

# Defina o preço de referência para o cálculo do ATM
rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 0, 1)
ref_price = rates[0][4]

# Busque os dados históricos de preços da ação usando o MetaTrader 5
data = pd.DataFrame(mt5.copy_rates_range(ticker, mt5.TIMEFRAME_D1, start_time, end_time))
data.drop(columns=['spread', 'real_volume'], inplace=True)
data.rename(columns={'time': 'date', 'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'tick_volume': 'Volume'}, inplace=True)
data.set_index('date', inplace=True)
data.index = pd.to_datetime(data.index, unit='s')

# Calcule a média móvel de 20 e 200 dias
data['SMA20'] = data['Close'].rolling(window=20).mean()
data['SMA200'] = data['Close'].rolling(window=200).mean()

# Calcule o RSI de 14 dias
delta = data['Close'].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
avg_gain = gain.rolling(window=14).mean()
avg_loss = loss.rolling(window=14).mean()
rs = avg_gain / avg_loss
data['RSI'] = 100 - (100 / (1 + rs))

# Calcule o ADX de 14 dias
high = data['High']
low = data['Low']
close = data['Close']
adx = mt5.iADX(ticker, mt5.TIMEFRAME_D1, 14, mt5.PRICE_MEDIAN)
data['ADX'] = adx[0]

# Calcule o DI+ e DI- de 14 dias
dip = mt5.iADX(ticker, mt5.TIMEFRAME_D1, 14, mt5.MODE_PLUSDI)
din = mt5.iADX(ticker, mt5.TIMEFRAME_D1, 14, mt5.MODE_MINUSDI)

data['DI+'] = dip[0]
data['DI-'] = din[0]

# Identifique a tendência
if data['Close'][-1] > data['SMA20'][-1] and data['Close'][-1] > data['SMA200'][-1] and data['SMA20'][-1] > data['SMA20'][-2] and data['SMA200'][-1] > data['SMA200'][-2] and data['RSI'][-1] > 50 and data['ADX'][-1] > 25 and data['DI+'][-1] > data['DI-'][-1]:
    trend = 'Bullish'
elif data['Close'][-1] < data['SMA20'][-1] and data['Close'][-1] < data['SMA200'][-1] and data['SMA20'][-1] < data['SMA20'][-2] and data['SMA200'][-1] < data['SMA200'][-2] and data['RSI'][-1] < 50 and data['ADX'][-1] > 25 and data['DI+'][-1] < data['DI-'][-1]:
    trend = 'Bearish'
else:
    trend = 'Neutral'

# Busque as opções disponíveis para o ticker escolhido
options = mt5.symbols_get(ticker)

# Identifique as opções do tipo PUT e CALL com data de expiração adequada e preço de exercício perto do dinheiro (ATM)
call_options = [option for option in options if option.option_type == mt5.OPTION_TYPE_CALL and option.expiration == expiration_date and abs(option.strike - ref_price) < ref_price * 0.05]
put_options = [option for option in options if option.option_type == mt5.OPTION_TYPE_PUT and option.expiration == expiration_date and abs(option.strike - ref_price) < ref_price * 0.05]

# Identifique a opção de CALL com menor preço de compra e a opção de PUT com menor preço de venda
best_call = min(call_options, key=lambda option: option.bid)
best_put = min(put_options, key=lambda option: option.ask)

# Calcule o preço teórico do Collar Longo
S = yf.download(ticker, start=start_time, end=end_time)['Adj Close'][-1]
Kc = best_call.strike
Kp = best_put.strike
T = (expiration_date - datetime.now()).days / 365
r = 0.01
sigma = data['Close'].pct_change().rolling(window=30).std().iloc[-1] * np.sqrt(252)
call_price = black_scholes(S, Kc, T, r, 'C', sigma)
put_price = black_scholes(S, Kp, T, r, 'P', sigma)
collar_price = call_price - put_price - best_call.ask + best_put.bid

# Verifique se o custo mensal do Collar Longo é inferior a 15% do custo de uma rolagem ATM
atm_call = min([option for option in call_options if option.strike >= ref_price], key=lambda option: option.bid)
atm_put = min([option for option in put_options if option.strike <= ref_price], key=lambda option: option.ask)
atm_cost = atm_call.bid - atm_put.ask
roll_cost = best_call.ask - atm_call.bid + atm_put.ask

if collar_price / T < 0.15 * atm_cost:
    print('Recomenda-se a estratégia Collar Longo para', ticker, 'com as seguintes opções:')
    print('Call:', best_call.symbol, 'Strike:', best_call.strike, 'Preço:', best_call.ask)
    print('Put:', best_put.symbol, 'Strike:', best_put.strike, 'Preço:', best_put.bid)
    print('Preço teórico do Collar Longo:', collar_price)
    print('Custo mensal do Collar Longo:', collar_price / T)
    print('Custo de uma rolagem ATM:', atm_cost)
    print('Custo da rolagem necessária:', roll_cost)
else:
    print('Não é recomendado o uso da estratégia Collar Longo para', ticker, 'no momento.')
