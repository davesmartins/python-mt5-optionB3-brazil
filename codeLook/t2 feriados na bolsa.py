import datetime
import pytz
import MetaTrader5 as mt5

# Conectar à plataforma MetaTrader 5
if not mt5.initialize():
    print("Erro ao inicializar a MetaTrader 5!")
    quit()

# Definir o parâmetro symbol para o contrato futuro de dólar
symbol = "WDOF21"

# Obter a hora local do servidor de negociação
server_time = mt5.time_trade_server()
print(server_time)

# Obter a data atual em UTC
utc_time = datetime.datetime.utcnow()

# Converter a hora local do servidor de negociação para o fuso horário UTC
local_tz = pytz.timezone("America/Sao_Paulo")
server_time = local_tz.localize(server_time)
utc_time = server_time.astimezone(pytz.utc)

# Obter o calendário de feriados da bolsa de valores B3 para o ano atual
year = utc_time.year
holidays = mt5.market_get_holidays("B3", year)

# Calcular a data de expiração do contrato futuro de dólar
expiration_date = datetime.datetime(year, 3, 1)  # Define a data de expiração inicial para o primeiro dia de março do ano atual
while True:
    # Se a data de expiração cair em um feriado, final de semana ou horário de verão, adicionar um dia útil
    if expiration_date in holidays or expiration_date.weekday() >= 5 or mt5.is_dst(expiration_date.timestamp()):
        expiration_date += datetime.timedelta(days=1)
    else:
        break

# Imprimir a data de expiração do contrato futuro de dólar
print("Data de expiração:", expiration_date.strftime("%Y-%m-%d"))

# Finalizar a conexão com a plataforma MetaTrader 5
mt5.shutdown()
