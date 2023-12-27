import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM

# Estabeleça conexão com o MetaTrader 5
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

# Baixe os dados históricos de preços da ação usando o MetaTrader 5
data = mt5.copy_rates_range(ticker, mt5.TIMEFRAME_D1, start_time, end_time)

# Converta os dados em um DataFrame do pandas
data = pd.DataFrame(data)
data['time'] = pd.to_datetime(data['time'], unit='s')
data.set_index('time', inplace=True)

# Crie um scaler para normalizar os dados
scaler = MinMaxScaler(feature_range=(0,1))

# Normalize os dados
scaled_data = scaler.fit_transform(data['close'].values.reshape(-1,1))

# Defina o tamanho da janela de tempo para previsões
window_size = 20

# Crie um array com as janelas de tempo para previsões
X = []
Y = []
for i in range(window_size, len(data)):
    X.append(scaled_data[i-window_size:i,0])
    Y.append(scaled_data[i,0])
X = np.array(X)
Y = np.array(Y)

# Divida os dados em conjuntos de treinamento e teste
split = int(len(X) * 0.8)
X_train = X[:split]
Y_train = Y[:split]
X_test = X[split:]
Y_test = Y[split:]

# Crie o modelo de rede neural
model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(X_train.shape[1],1)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

# Compile o modelo
model.compile(optimizer='adam', loss='mean_squared_error')

# Treine o modelo
model.fit(X_train, Y_train, batch_size=1, epochs=1)

# Faça as previsões com base nos dados de teste
predictions = model.predict(X_test)
predictions = scaler.inverse_transform(predictions)

# Exiba o gráfico com as previsões
plt.figure(figsize=(12,6))
plt.plot(data['close'].index[split:], Y_test, label='Preço real')
plt.plot(data['close'].index[split:], predictions, label='Previsão')
plt.legend()
plt.show()

# Encerre a conexão com o MetaTrader 5
mt5.shutdown()
