import MetaTrader5 as mt5
import pandas as pd

# Conecte-se ao MetaTrader 5
if not mt5.initialize():
    print("Falha na conexão ao MetaTrader 5")
    quit()

# Defina o símbolo do ativo subjacente
symbol = "PETR4"

# Obtenha as informações das opções disponíveis
options = mt5.symbols_get(group=symbol, option=True)
# print(options)
# Crie um DataFrame para armazenar as informações das opções
df_options = pd.DataFrame(columns=["symbol", "strike", "type", "last", "bid", "ask"])

# Obtenha o preço de mercado atual do ativo subjacente
print(mt5.symbol_info_tick(symbol))
market_price = mt5.symbol_info_tick(symbol).last

# Percorra todas as opções e filtre as que correspondem ao perfil de collar
for option in options:
    print(option)
    if option.description.startswith("PETR4") and option.expiration_mode == mt5.EXPIRATION_MODE_EXCHANGE:
        
        # Obtenha as informações da opção
        symbol_option = option.name
        strike = option.option_strike
        option_type = option.option_type
        last = mt5.symbol_info_tick(symbol_option).last
        bid = mt5.symbol_info_tick(symbol_option).bid
        ask = mt5.symbol_info_tick(symbol_option).ask
        
        # Verifique se o preço de exercício está próximo ao preço de mercado
        strike_range = 0.1 * market_price
        if strike - strike_range <= market_price <= strike + strike_range:
            
            # Calcule o custo do collar
            put_price = ask
            call_price = mt5.symbol_info_tick(symbol_option.replace("P", "C")).bid
            collar_cost = call_price - put_price
            
            # Verifique se o custo do collar é menor que R$0,30
            if collar_cost < 0.30:
                
                # Adicione as informações da opção ao DataFrame
                df_options = df_options.append({"symbol": symbol_option, "strike": strike, "type": option_type, "last": last, "bid": bid, "ask": ask, "collar_cost": collar_cost}, ignore_index=True)

# Imprima na tela as informações das opções que atendem aos critérios definidos
print("Opções que atendem aos critérios de collar:")
print(df_options)

# Desconecte-se do MetaTrader 5
mt5.shutdown()
