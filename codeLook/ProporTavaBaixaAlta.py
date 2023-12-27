import pandas as pd
import MetaTrader5 as mt5
from ta.volatility import BollingerBands
from sklearn.linear_model import LinearRegression

# Estabeleça conexão com o MetaTrader 5
mt5.initialize()

# Defina o ticker da ação e o intervalo de tempo desejado
ticker = 'PETR4'
start_time = datetime(2020, 1, 1)
end_time = datetime(2023, 4, 30)

# Busque os dados históricos de preços da ação usando o MetaTrader 5
data = mt5.copy_rates_range(ticker, mt5.TIMEFRAME_D1, start_time, end_time)

# Converta os dados em um DataFrame do pandas e calcule as bandas de Bollinger
df = pd.DataFrame(data)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.set_index('time', inplace=True)
bb = BollingerBands(close=df['close'], window=20, window_dev=2)
df['bb_high'] = bb.bollinger_hband()
df['bb_low'] = bb.bollinger_lband()

# Use uma regressão linear para determinar a tendência do ativo
x = np.array(df.index).reshape(-1, 1)
y = np.array(df['close'])
reg = LinearRegression().fit(x, y)
slope = reg.coef_[0]

# Determine se a tendência é de alta ou de baixa
if slope > 0:
    trend = 'alta'
else:
    trend = 'baixa'

# Calcule a volatilidade dos preços da ação
std = df['close'].std()

# Sugira uma estratégia de opção com base na tendência e na volatilidade
if trend == 'alta' and std > 0.5:
    print(f"Sugestão: trava de alta (bull spread) em opções de compra.")
elif trend == 'baixa' and std > 0.5:
    print(f"Sugestão: trava de baixa (bear spread) em opções de venda.")
else:
    print("Não há sugestão de estratégia no momento.")
