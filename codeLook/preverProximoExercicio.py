import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime
from sklearn.linear_model import LinearRegression

import json 
from io import StringIO

with open("config.json") as json_data_file:
    data = json.load(json_data_file)
# Estabeleça conexão com o MetaTrader 5
mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password'])

# Busque os dados históricos de preços da ação usando o MetaTrader 5
#data = mt5.copy_rates_range(ticker, mt5.TIMEFRAME_D1, start_time, end_time)



# Definir as variáveis ​​de entrada
ticker = 'PETR4'  # Ticker do ativo
start_time = datetime(2021, 1, 1)  # Data de início do histórico de preços
end_time = datetime(2023, 4, 28)  # Data final do histórico de preços
expiration_date = datetime(2023, 4, 21)  # Data de expiração da opção
option_type = 'call'  # Tipo de opção (call ou put)
strike_price = 25.0  # Preço de exercício da opção


# Selecionar o timeframe e obter o histórico de preços do ativo
timeframe = mt5.TIMEFRAME_D1
data = mt5.copy_rates_range(ticker, timeframe, start_time, end_time)

# Converter os dados em um DataFrame
df = pd.DataFrame(data)
df['time'] = pd.to_datetime(df['time'], unit='s')
df = df.set_index('time')

# Calcular o retorno diário
df['Daily Return'] = df['close'].pct_change()

# Calcular a média móvel de 20 dias
df['SMA20'] = df['close'].rolling(window=20).mean()

# Selecionar os dados a partir do último dia de negociação
last_day_data = df.loc[str(end_time.date())]

# Selecionar o preço de fechamento da última data de negociação
last_day_close_price = last_day_data['close']

# Selecionar o preço de fechamento da data de expiração da opção
expiration_date_data = df.loc[str(expiration_date.date())]
expiration_date_close_price = expiration_date_data['close']

# Selecionar o retorno diário para o período entre a última data de negociação e a data de expiração da opção
daily_returns = expiration_date_data['Daily Return'].values

# Selecionar o índice do preço de fechamento da última data de negociação
last_day_index = df.index.get_loc(str(end_time.date()))

# Selecionar o índice da data de expiração da opção
expiration_date_index = df.index.get_loc(str(expiration_date.date()))

# Selecionar os dados para o período entre a última data de negociação e a data de expiração da opção
data_subset = df.iloc[last_day_index+1:expiration_date_index+1]

# Calcular o preço máximo e mínimo durante o período de tempo selecionado
price_max = data_subset['close'].max()
price_min = data_subset['close'].min()

# Criar um dataframe com as variáveis de entrada
input_data = pd.DataFrame({
    'last_day_close_price': [last_day_close_price],
    'price_max': [price_max],
    'price_min': [price_min]
})

# Criar um modelo de regressão linear
reg = LinearRegression()

# Treinar o modelo
reg.fit(input_data, daily_returns)

# Prever o retorno diário no próximo exercício de opção
next_option_expiration_data = df.loc[str(expiration_date.date())]
next_option_expiration_close_price = next_option_expiration_data['close']
input_data_next = pd.DataFrame({
    'last_day_close_price': [last_day_close_price],
    'price_max': [next_option_expiration_data['close'].max()],
    'price_min': [next_option_expiration_data['close'].min()]
})
next_option_daily_return = reg.predict(input_data_next)

# Calcular o preço da ação no próximo exercício de opção
next_option_price = next_option_expiration_close_price * (1 + next_option_daily_return)

# Imprimir o preço da ação no próximo exercício de opção
print(f'O preço da ação no próximo exercício de opção é de R$ {next_option_price:.2f}.')

