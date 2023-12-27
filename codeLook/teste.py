import MetaTrader5 as mt5

# Conecte-se ao MetaTrader 5
if not mt5.initialize():
    print("Falha na conexão ao MetaTrader 5")
    quit()

# Defina o símbolo da opção
symbol = "PETR4F210430"

# Obtenha a profundidade do book de ofertas
depth = 10 # Defina a profundidade desejada
ticks = mt5.copy_ticks_from(symbol, mt5.TIME_TYPE_TICK, depth, mt5.COPY_TICKS_ALL)

# Obtenha as informações do símbolo
symbol_info = mt5.symbol_info(symbol)
strike = symbol_info.option_strike
option_type = "americana" if symbol_info.option_type == mt5.OPTION_EXERCISE_AMERICAN else "europeia"

# Exiba as informações do book de ofertas e do símbolo na tela
print("Symbol:", symbol, "\tStrike:", strike, "\tTipo:", option_type)
for tick in ticks:
    print("\tBid:", tick.bid, "\tAsk:", tick.ask)

# Desconecte-se do MetaTrader 5
mt5.shutdown()
