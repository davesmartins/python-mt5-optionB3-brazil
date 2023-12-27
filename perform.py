import datetime
import MetaTrader5 as mt5
import time

# Conectando-se ao MetaTrader 5
mt5.initialize(login=901367912, server="OramaDTVM-Server",password="Ftgh173z-")
# mt5.initialize()

# Obtendo o tempo de execução para symbol_info_tick
start_time = time.time()
symbol_info = mt5.symbol_info_tick("PETR4")
end_time = time.time()
print(f"symbol_info_tick tempo de execucao: {int(end_time ) - int(start_time ) } segundos")
print(f"symbol_info_tick: {symbol_info}")

print("==================================================")

start_time = time.time()
ctf = mt5.copy_ticks_from("PETR4", time.time(), 1, mt5.COPY_TICKS_ALL)
end_time = time.time()
print(f"copy_tick_from tempo de execução: {end_time - start_time} segundos")
print(f"copy_tick_from: {ctf}")


print("==================================================")
# Obtendo o tempo de execução para copy_rates_from
start_time = time.time()
copy_info = mt5.copy_rates_from("PETR4", mt5.TIMEFRAME_M1, time.time() , 1)
end_time = time.time()
print(f"copy_rates_from tempo de execucao: {int(end_time ) - int(start_time ) } segundos")
print(f"copy_rates_from: {copy_info}")

# Finalizando a conexão com o MetaTrader 5
mt5.shutdown()
