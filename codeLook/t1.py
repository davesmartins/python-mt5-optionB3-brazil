import MetaTrader5 as mt5
import pandas as pd

# conecte-se ao MetaTrader 5
if not mt5.initialize():
    print("initialize() failed")
    quit()

# defina o símbolo do ativo subjacente
symbol = "PETR"

# obtenha as informações de todos as opções disponíveis
options = mt5.symbols_get(group=symbol) #(group=symbol, option=True)
print(len(options))

# crie um dataframe para armazenar as informações de todas as opções
df_options = pd.DataFrame(columns=["symbol", "strike", "type", "last", "bid", "ask", "expiration"])

# percorra todas as opções e adicione as informações ao dataframe
for option in options:
    selected=mt5.symbol_select(option.name,True)
    print(option)
    print(option.description, option.name, option.basis , option.expiration_mode)
    if option.description.startswith("PETR") :
        symbol_option = option.name
        strike = option.option_strike
        option_type = option.option_type
        last = mt5.symbol_info_tick(symbol_option).last
        bid = mt5.symbol_info_tick(symbol_option).bid
        ask = mt5.symbol_info_tick(symbol_option).ask
        expiration = option.expiration
        df_options = df_options.append({"symbol": symbol_option, "strike": strike, "type": option_type, "last": last, "bid": bid, "ask": ask, "expiration": expiration}, ignore_index=True)

# filtre as opções que atendem aos critérios de collar
df_collar = df_options[df_options["type"] == mt5.ORDER_TYPE_SELL].copy()
df_collar["call"] = ""
df_collar["put"] = ""

for index, row in df_collar.iterrows():
    call_name = row["symbol"].replace("P", "C")
    if call_name in df_collar["symbol"].values:
        df_collar.loc[index, "call"] = call_name

df_collar.dropna(inplace=True)
df_collar = df_collar[df_collar["strike"] < df_collar["call"].apply(lambda x: float(x[7:])).values]
df_collar = df_collar[df_collar["put"] < df_collar["strike"].values + 0.30]
df_collar = df_collar[df_collar["call"].apply(lambda x: float(x[7:])).values < df_collar["strike"].values + 0.30]
df_collar = df_collar[df_collar["put"] > df_collar["strike"].values - 0.30]
df_collar = df_collar[df_collar["call"].apply(lambda x: float(x[7:])).values > df_collar["strike"].values - 0.30]

# imprima as informações das opções que atendem aos critérios de collar
print(df_collar)

# desconecte-se do MetaTrader 5
mt5.shutdown()
