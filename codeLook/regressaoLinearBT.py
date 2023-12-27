import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression


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

# Converta os dados em um DataFrame do pandas
data = pd.DataFrame(data)
data['time'] = pd.to_datetime(data['time'], unit='s')
data.set_index('time', inplace=True)

# Calcule os retornos diários da ação
data['Returns'] = data['close'].pct_change()

# Calcule a média móvel de 20 dias
data['SMA20'] = data['close'].rolling(window=20).mean()

# Remova as primeiras 20 linhas (que não têm média móvel)
data = data.dropna()

# Divida os dados em conjuntos de treinamento e teste
split = int(len(data) * 0.8)
train_data = data[:split]
test_data = data[split:]

# Ache as terceiras quintas-feiras de cada mês
third_thursdays = pd.date_range(start_time, end_time, freq='WOM-3THU').strftime('%Y-%m-%d')

# Filtrar o conjunto de testes para apenas incluir dias de terceira quinta-feira
test_data = test_data.loc[test_data.index.isin(third_thursdays)]

# Defina as variáveis independentes (X) e dependentes (Y) para o conjunto de treinamento
X_train = train_data[['SMA20', 'Returns']].values
Y_train = train_data['close'].values

# Crie o modelo de regressão linear e ajuste-o aos dados de treinamento
reg = LinearRegression()
reg.fit(X_train, Y_train)

# Faça as previsões com base nos dados de teste
X_test = test_data[['SMA20', 'Returns']].values
Y_test_pred = reg.predict(X_test)

# Calcule os preços de fechamento na terceira quinta-feira do mês
Y_test_actual = test_data['close'].values

print(test_data.index)
print(Y_test_pred)
print(Y_test_actual)
print(Y_test_pred)

# Exiba os resultados do backtest
plt.figure(figsize=(12,6))
plt.plot(test_data.index, Y_test_actual, label='Preço real')
plt.plot(test_data.index, Y_test_pred, label='Previsão')
plt.legend()
plt.show()


# Encerre a conexão com o MetaTrader 5
mt5.shutdown()
