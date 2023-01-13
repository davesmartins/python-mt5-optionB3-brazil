import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import json 
from io import StringIO
# import pytz module for working with time zone
import pytz
import requests

pd.set_option('display.max_columns', 500) # number of columns to be displayed
pd.set_option('display.width', 1500)      # max table width to display

timezone = pytz.timezone("Etc/UTC")

with open("config.json") as json_data_file:
    data = json.load(json_data_file)

def send_to_telegram(message):

    apiToken = data['telegram']['token'] # '5082654068:AAF7quCLZ4xuTq2FBdo3POssdJsM_FRHwTs'
    chatID = data['telegram']['chatID'] # '515382482'
    apiURL = f'https://api.telegram.org/bot{apiToken}/sendMessage'

    try:
        response = requests.post(apiURL, json={'chat_id': chatID, 'text': message})
        print(response.text)
    except Exception as e:
        print(e)


def getInfoOpcoes(ativo):
    
    symbols=mt5.symbols_get( ativo )
    df = pd.DataFrame(symbols, columns =["custom","chart_mode","select","visible","session_deals","session_buy_orders","session_sell_orders","volume","volumehigh","volumelow","time","digits","spread",
                                         "spread_floa","ticks_bookdepth","trade_calc_mode","trade_mode","start_time","expiration_time","trade_stops_level","trade_freeze_level","trade_exemode","swap_mode",
                                         "swap_rollover3days","margin_hedged_use_leg","expiration_mode","filling_mode","order_mode","order_gtc_mode","option_mode","option_right","bid","bidhigh","bidlow",
                                         "ask","askhigh","asklow","last","lasthigh","lastlow","volume_real","volumehigh_real","volumelow_real","option_strike","point","trade_tick_value","trade_tick_value_profit",
                                         "trade_tick_value_loss","trade_tick_size","trade_contract_size","trade_accrued_interest","trade_face_value","trade_liquidity_rate","volume_min","volume_max","volume_step",
                                         "volume_limit","swap_long","swap_short","margin_initial","margin_maintenance","session_volume","session_turnover","session_interest","session_buy_orders_volume",
                                         "session_sell_orders_volume","session_open","session_close","session_aw","session_price_settlement","session_price_limit_min","session_price_limit_max","margin_hedged",
                                         "price_change","price_volatility","price_theoretical","price_greeks_delta","price_greeks_theta","price_greeks_gamma","price_greeks_vega","price_greeks_rho",
                                         "price_greeks_omega","price_sensitivity","basis","category","currency_base","currency_profit","currency_margin","bank","description","exchange","formula","isin","name",
                                         "page","path"])
    # print(symbols[:1])
    # print(df)
    df.drop(["custom","chart_mode","select","visible","session_deals","session_buy_orders","session_sell_orders","volume","volumehigh","volumelow","time","digits","spread","spread_floa","ticks_bookdepth",
            "trade_calc_mode","trade_mode","start_time","trade_stops_level","trade_freeze_level","trade_exemode","swap_mode","swap_rollover3days","margin_hedged_use_leg","expiration_mode",
            "filling_mode","order_mode","order_gtc_mode","bid","bidhigh","bidlow","ask","askhigh","asklow","last","lasthigh","lastlow","volume_real","volumehigh_real","volumelow_real",
            "point","trade_tick_value","trade_tick_value_profit","trade_tick_value_loss","trade_tick_size","trade_contract_size","trade_accrued_interest","trade_face_value","trade_liquidity_rate",
            "volume_min","volume_max","volume_step","volume_limit","swap_long","swap_short","margin_initial","margin_maintenance","session_volume","session_turnover","session_interest","session_buy_orders_volume",
            "session_sell_orders_volume","session_open","session_close","session_aw","session_price_settlement","session_price_limit_min","session_price_limit_max","margin_hedged","price_change","price_volatility",
            "price_theoretical","price_greeks_delta","price_greeks_theta","price_greeks_gamma","price_greeks_vega","price_greeks_rho","price_greeks_omega","price_sensitivity","category","currency_base",
            "currency_profit","currency_margin","bank","formula","isin","page", "path", "exchange"],
                        axis=1, inplace=True)
    # print(df)
    df['option_strike'] = df['option_strike'].astype(float)
    df['expiration_time'] = pd.to_datetime(df['expiration_time'], unit="s") 
    df = df.query('option_strike > 0', engine='python')
    df['letraVenc'] = df['name'].str[4:5]
    df['option_right'] =  df.apply(lambda x:  table_call_put(x['option_right']) , axis=1)  
    df['option_mode'] =  df.apply(lambda x:  table_tipo(x['option_mode']) , axis=1) 
    df['mesVenc'] =  df.apply(lambda x:  table_mes(x['letraVenc']) , axis=1)  
    df['tick'] = df.apply(lambda x:  retrieve_latest_tick(x['name']) , axis=1)   
    df['price'] = df.apply(lambda x:  retrieve_latest_tick(x['basis'])['last'] , axis=1)  
    df['bid'] =  0
    df['ask'] =  0
    df['volume'] = 0
    df['implicito'] = df.apply(lambda x:  getImplicito(x) , axis=1) 
    df['time_tick'] = ''  
    
    for idx in df.index:
        try:            
            df['bid'][idx] = df['tick'][idx]['bid'] 
            df['ask'][idx] = df['tick'][idx]['ask'] 
            df['volume'][idx] = df['tick'][idx]['volume'] 
            df['time_tick'][idx] = df['tick'][idx]['time']
        except:  
            df['bid'][idx] = 0
            df['ask'][idx] = 0
            df['volume'][idx] =0 
            df['time_tick'][idx] = ''  
        
    df.drop(["tick"],  axis=1, inplace=True) 
    
    df = df.query('ask > 0 and bid > 0', engine='python')
         
    return df  

 
def retrieve_latest_tick(symbol):
    # Retrieve the tick information
    # tick = mt5.symbol_info_tick(symbol)
    # return tick
    # dataHoje = pd.Timestamp(datetime(2023, 1, 11).strftime('%Y-%m-%d')+" 18:00:00") 
    dataHoje =  pd.Timestamp(datetime.today().strftime('%Y-%m-%d %H:%M') ) 
    # print(dataHoje)
    if (dataHoje.hour < 10):
        dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=18,minute=0)
    else: 
        if (dataHoje.hour >= 18):
            dataHoje = dataHoje.replace(hour=18,minute=0)
    # print(dataHoje)
    ticks = mt5.copy_ticks_from(symbol, dataHoje, 1, mt5.COPY_TICKS_ALL)
    # print("Ticks received:",(ticks))
    v = pd.DataFrame(ticks)
    v['time'] = pd.to_datetime(v['time'] , unit='s')
    return v

def getImplicito(v): 
    if (v['option_right'] == 'CALL' ):  
        if ( v['option_strike'] >= v['price']):
            return 0
        else: 
            return v['price'] - v['option_strike']
    else: 
        if (v['option_right'] == 'PUT' ):  
            if ( v['option_strike'] <= v['price']):
                return 0
            else: 
                return v['option_strike'] - v['price']   


def table_tipo(valor):    
    if (valor == mt5.SYMBOL_OPTION_MODE_EUROPEAN):
        return 'EUROPEIA'
    else:
        if (valor == mt5.SYMBOL_OPTION_MODE_AMERICAN):
            return 'AMERICANA'
        else:
            return '-' 

def table_call_put(valor):    
    if (valor == mt5.SYMBOL_OPTION_RIGHT_CALL):
        return 'CALL'
    else:
        if (valor == mt5.SYMBOL_OPTION_RIGHT_PUT):
            return 'PUT'
        else:
            return '-'    

        
def table_mes(valor):
    if valor in ['A','M']:
        return 'JANEIRO'
    if valor in ['B','N']:
        return 'FEVEREIRO'
    if valor in ['C','O']:
        return 'MARÇO'
    if valor in ['D','P']:
        return 'ABRIL'
    if valor in ['E','Q']:
        return 'MAIO'
    if valor in ['F','R']:
        return 'JUNHO'
    if valor in ['G','S']:
        return 'JULHO'
    if valor in ['H','T']:
        return 'AGOSTO'
    if valor in ['I','U']:
        return 'SETEMBRO'
    if valor in ['J','V']:
        return 'OUTUBRO'
    if valor in ['K','W']:
        return 'NOVEMBRO'
    if valor in ['L','X']:
        return 'DEZEMBRO'
    
    return '-'

def getSBTH(op):
    
    return 0

# establish connection to the MetaTrader 5 terminal

# exibimos dads sobre o pacote MetaTrader5
print("MetaTrader5 package author: ",mt5.__author__)
print("MetaTrader5 package version: ",mt5.__version__)
 
# estabelecemos a conexão com o terminal MetaTrader 5 para a conta especificada
if not mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password']):
    print("initialize() failed, error code =",mt5.last_error())
    quit()
 
# imprimimos informações sobre o estado da conexão, o nome do servidor e a conta de negociação
# print(mt5.terminal_info())
# imprimimos informações sobre a versão do MetaTrader 5
# print(mt5.version())


if __name__ == '__main__':
    timeNow = datetime.now().hour

    print("run ",mt5.version())

    send_to_telegram("Robô procurando oportunidades!")
    
    acoes = ['CPLE', 'MRFG', 'MGLU', 'USIM']
    
    for ac in acoes:

        opcoes= getInfoOpcoes(ac)        
        print(opcoes)        
        vSBTH = getSBTH( opcoes )
        
        print(vSBTH)
      
    
mt5.shutdown()
