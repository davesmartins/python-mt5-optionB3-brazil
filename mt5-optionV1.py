import time
import sys, gc
import concurrent.futures
import traceback
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import json 
from io import StringIO
# import pytz module for working with time zone
import pytz
import requests
import locale 
from bcb import sgs

QTDE = 100

pd.set_option('mode.chained_assignment', None)
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
        # print(response.text)
    except Exception as e:
        print(e)

# letras = [['A','M'],['B','N'],['C','O'],['D','P'],['E','Q'],['F','R'],['G','S'],['H','T'],['I','U'],['J','V'],['K','W'],['L','X']]
letras = [['B','N'],['C','O'],['D','P'],['E','Q'],['F','R'],['G','S'],['H','T'],['I','U'],['J','V'],['K','W'],['L','X']]

def getInfoOpcoes(ativo):    
    try:        
        symbols=mt5.symbols_get( ativo )
        df = converter(symbols)
        print(ativo, len(df))
        if (len(df) <= 0):
            return df 
         
        # selected=mt5.symbol_select(df['basis'][0],True) 
        # if not selected:
        #     print("ERROR ",mt5.last_error())
        #     mt5.shutdown()
        #     quit()   
        lasttick=mt5.symbol_info_tick("MGLU3")               
        preco = lasttick['last']            
                       
        df.drop(["custom","chart_mode","select","visible","session_deals","session_buy_orders","session_sell_orders","volume","volumehigh","volumelow","time","digits","spread","spread_floa","ticks_bookdepth",
                "trade_calc_mode","trade_mode","start_time","trade_stops_level","trade_freeze_level","trade_exemode","swap_mode","swap_rollover3days","margin_hedged_use_leg","expiration_mode",
                "filling_mode","order_mode","order_gtc_mode","bid","bidhigh","bidlow","ask","askhigh","asklow","last","lasthigh","lastlow","volume_real","volumehigh_real","volumelow_real",
                "point","trade_tick_value","trade_tick_value_profit","trade_tick_value_loss","trade_tick_size","trade_contract_size","trade_accrued_interest","trade_face_value","trade_liquidity_rate",
                "volume_min","volume_max","volume_step","volume_limit","swap_long","swap_short","margin_initial","margin_maintenance","session_volume","session_turnover","session_interest","session_buy_orders_volume",
                "session_sell_orders_volume","session_open","session_close","session_aw","session_price_settlement","session_price_limit_min","session_price_limit_max","margin_hedged","price_change","price_volatility",
                "price_theoretical","price_greeks_delta","price_greeks_theta","price_greeks_gamma","price_greeks_vega","price_greeks_rho","price_greeks_omega","price_sensitivity","category","currency_base",
                "currency_profit","currency_margin","bank","formula","isin","page", "path", "exchange"],
                            axis=1, inplace=True)
        
        # df = df.query(f"(option_strike > 0) & (basis == '{ativo}')", engine='python')
        df = df.query(f"(option_strike > 0)", engine='python')
        df['expiration_time'] = pd.to_datetime(df['expiration_time'], unit="s")
        # print("--> ", len(df))
        # df['option_strike'] = df['option_strike'].astype(float)   
        
        df['letraVenc'] = df['name'].str[4:5]
        df['option_right'] =  df.apply(lambda x:  table_call_put(x['option_right']) , axis=1)  
        df['option_mode'] =  df.apply(lambda x:  table_tipo(x['option_mode']) , axis=1) 
        df['mesVenc'] =  df.apply(lambda x:  table_mes(x['letraVenc']) , axis=1)  
        df['tick'] = df.apply(lambda x:  retrieve_latest_tick(x['name']) , axis=1)           
        df['price'] = preco
        df['bid'] =  0  
        df['ask'] =  0
        df['last'] =  0
        df['intrinseco'] =  0
        df['extrinseco'] =  0
        df['volume'] = 0
        df['time_tick'] = '' 
        df['vencimento'] = pd.to_datetime(df['expiration_time'], unit="s").dt.strftime("%d/%m/%Y") 
        
        for idx in df.index:
            try:     
                if (not df['tick'][idx].empty):       
                    df['bid'][idx] = float(df['tick'][idx]['bid'] ) 
                    df['ask'][idx] = float(df['tick'][idx]['ask'] ) 
                    df['last'][idx] = float(df['tick'][idx]['last'] )  
                    df['volume'][idx] = int(df['tick'][idx]['volume'] ) 
                    df['time_tick'][idx] = df['tick'][idx]['time']
            except:  
                df['bid'][idx] = 0
                df['ask'][idx] = 0
                df['last'][idx] = 0
                df['volume'][idx] =0 
                df['time_tick'][idx] = ''  

        df.drop(["tick"],  axis=1, inplace=True) 
        df['intrinseco'] = df.apply(lambda x:  getIntrinseco(x) , axis=1) 
        df['extrinseco'] = df.apply(lambda x:  getExtrinseco(x) , axis=1) 

        df = df.query('ask > 0 and bid > 0', engine='python')
        # print("--> ", len(df))
        df = df.sort_values(['option_strike'],
              ascending = [True])
        
        return df 
    except Exception:
        traceback.print_exc()
        # return pd.DataFrame()
      
def getSelic():
    selic = sgs.get({'selic':432}, start = '2023-01-21')
    # print(type(selic) )
    return float(selic['selic'][0] )
    # return sgs.get({'selic':432}, start = '2023-01-20')

def converter(ativos):
    return pd.DataFrame(ativos, 
                        columns =["custom","chart_mode","select","visible","session_deals","session_buy_orders","session_sell_orders","volume","volumehigh","volumelow","time","digits","spread",
                                        "spread_floa","ticks_bookdepth","trade_calc_mode","trade_mode","start_time","expiration_time","trade_stops_level","trade_freeze_level","trade_exemode","swap_mode",
                                        "swap_rollover3days","margin_hedged_use_leg","expiration_mode","filling_mode","order_mode","order_gtc_mode","option_mode","option_right","bid","bidhigh","bidlow",
                                        "ask","askhigh","asklow","last","lasthigh","lastlow","volume_real","volumehigh_real","volumelow_real","option_strike","point","trade_tick_value","trade_tick_value_profit",
                                        "trade_tick_value_loss","trade_tick_size","trade_contract_size","trade_accrued_interest","trade_face_value","trade_liquidity_rate","volume_min","volume_max","volume_step",
                                        "volume_limit","swap_long","swap_short","margin_initial","margin_maintenance","session_volume","session_turnover","session_interest","session_buy_orders_volume",
                                        "session_sell_orders_volume","session_open","session_close","session_aw","session_price_settlement","session_price_limit_min","session_price_limit_max","margin_hedged",
                                        "price_change","price_volatility","price_theoretical","price_greeks_delta","price_greeks_theta","price_greeks_gamma","price_greeks_vega","price_greeks_rho",
                                        "price_greeks_omega","price_sensitivity","basis","category","currency_base","currency_profit","currency_margin","bank","description","exchange","formula","isin","name",
                                        "page","path"])

def getSBTH(op):    
    resp = """
••••••••••••••••••••••••••••••••••••••••••••••••
 SBTH
••••••••••••••••••••••••••••••••••••••••••••••••
Ativo: **{ativo}**         🗓 {venc}
Montagem : 💵 **R$ {valor}** 
Ganho :  {percGanho}%  R$ {ganho}  
Ganho mensal : {percGanhoM}%
+ {rol} rolagens
CDI {dias} dias : {cdiPeriodo}%
Selic anual: {selic}

🅲 {ativo}   R$ {cot} - {qtde}(qtd)

🅲 {opr}  R$ {strike} - {qtde}(qtd)
    Últ. {last} Bid {bid} Ask {ask}  
    Percentual acima do papel {percAcima}%  
    
✳️ Intrínseco R$ {intri} 
👉 Ask {abIntri} abaixo do Intrínseco        

"""
    opc = op[ ( (op['option_right'] == "PUT")  & (op['option_strike'] >= (op['price']+op['ask'])) ) ]
    for idx in opc.index:            
            precoCompra = ( ((opc['price'][idx]+opc["ask"][idx])) * QTDE )
            diffInt = opc["intrinseco"][idx] - opc["ask"][idx]
            ganho = ((diffInt )/( precoCompra / QTDE ))*100
            d2 = datetime.strptime(opc['vencimento'][idx], '%d/%m/%Y')
            vdias = abs(( d2 - datetime.today() ).days)
            vMes = ((vdias-(vdias%30))/30)
            cdi = ((getSelic()/360)* vdias)
            perAc = ((opc['option_strike'][idx] - opc['price'][idx])/ opc['price'][idx])*100
            
            send_to_telegram( resp.format(
                ativo=opc['basis'][idx],
                venc= opc['vencimento'][idx] ,
                valor="{:,.2f}".format( precoCompra ),
                cot="{:,.2f}".format(opc['price'][idx]),
                opr=opc["name"][idx],
                strike="{:,.2f}".format(opc["option_strike"][idx]),
                intri="{:,.2f}".format(opc["intrinseco"][idx]),
                bid="{:,.2f}".format(opc["bid"][idx]),
                ask="{:,.2f}".format(opc["ask"][idx]),
                last="{:,.2f}".format(opc["last"][idx]),
                abIntri="{:,.2f}".format( diffInt ),
                ganho="{:,.2f}".format( (diffInt) * QTDE ),
                percGanho="{:,.2f}".format( ganho ),
                percGanhoM="{:,.2f}".format( ganho/(vMes+1) ),
                qtde=QTDE,
                dias= vdias,
                cdiPeriodo = "{:,.2f}".format( cdi ),
                percAcima  = "{:,.2f}".format( perAc ),
                rol="{:,.2f}".format(vMes+1),
                selic=getSelic()
            ) )
 
def retrieve_latest_tick(symbol):
    # dataHoje = pd.Timestamp(datetime(2023, 1, 11).strftime('%Y-%m-%d')+" 18:00:00")  
    dataHoje =  pd.Timestamp(datetime.today().strftime('%Y-%m-%d %H:%M:%S') ) 
    # print(symbol, dataHoje)
    # if (dataHoje.hour < 10):
    #     dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=10,minute=0)
         
    # if (dataHoje.isoweekday() == 6):
    #     dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=10,minute=0)
    # else:    
    #     if (dataHoje.isoweekday() == 7):
    #         dataHoje = dataHoje.replace(day=dataHoje.day-2, hour=10,minute=0)
        
    if (dataHoje.hour < 10):
        dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=10,minute=00)
    
    if (dataHoje.isoweekday() == 6):
        dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=10,minute=00)
    else:    
        if (dataHoje.isoweekday() == 7):
            dataHoje = dataHoje.replace(day=dataHoje.day-2, hour=10,minute=00)

    # dataHoje = dataHoje.replace(minute=dataHoje.minute-5)
    # count = 0
    # while True:
    #     ticks = mt5.copy_ticks_from(symbol, dataHoje,30, mt5.COPY_TICKS_ALL)  
    #     count = count+1
    #     if ((len(ticks) >=1) or (count>= 8)):
    #         break
    #     else:
    #         dataHoje = dataHoje - timedelta(minutes = 5) 
            
            #  datetime.datetime.now() - datetime.timedelta(minutes=15)
     
    # if (len(ticks) ==0):  
    dataHoje = dataHoje.replace(hour=10,minute=0)
    dataHoje1 = dataHoje.replace(hour=18,minute=00)
    # print("Price -> ",dataHoje, dataHoje1)
    ticks = mt5.copy_ticks_range(symbol, dataHoje,dataHoje1, mt5.COPY_TICKS_ALL)
    # dataHoje = dataHoje.replace(hour=10,minute=0)
    # dataHoje1 = dataHoje.replace(hour=18,minute=0)
    # print(dataHoje, dataHoje1)
    # ticks = mt5.copy_ticks_range(symbol, dataHoje,dataHoje1, mt5.COPY_TICKS_ALL)
    # print("Ticks received:",(ticks))
    if (type(ticks) == 'NoneType'):
            return pd.DataFrame()
    v = pd.DataFrame(ticks)
    v['time'] = pd.to_datetime(v['time'] , unit='s')
    # print("Tick -> ",v.tail(1))
    return v.tail(1)

def retrieve_latest_price(symbol):
    dataHoje =  pd.Timestamp(datetime.today().strftime('%Y-%m-%d %H:%M:%S') ) 
    # print(dataHoje)
    if (dataHoje.hour < 10):
        dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=10,minute=00)
    
    if (dataHoje.isoweekday() == 6):
        dataHoje = dataHoje.replace(day=dataHoje.day-1, hour=10,minute=00)
    else:    
        if (dataHoje.isoweekday() == 7):
            dataHoje = dataHoje.replace(day=dataHoje.day-2, hour=10,minute=00)
    try:  
        dataHoje = dataHoje.replace(hour=10,minute=0) 
        dataHoje1 = dataHoje.replace(hour=18,minute=00)
        # print("Price -> ",dataHoje, dataHoje1)
        ticks = mt5.copy_ticks_range(symbol, dataHoje,dataHoje1, mt5.COPY_TICKS_ALL)
        # dataHoje = dataHoje.replace(minute=dataHoje.minute-5)
        # ticks = mt5.copy_ticks_from(symbol, dataHoje,30, mt5.COPY_TICKS_ALL)
        # print("Ticks received:",(ticks))

        if (type(ticks) == 'NoneType'):
            return 0
        v = pd.DataFrame(ticks)
        # v['time'] = pd.to_datetime(v['time'] , unit='s')
        # print(v.tail(1))
        if (v.empty):
            return 0
        else:
            # print("Price -> ",v.tail(1)['last']  )
            return v.tail(1)['last']    
    except Exception:
        traceback.print_exc()
        return 0

def getIntrinseco(v): 
    if (v['option_right'] == 'CALL' ):  
        if ( v['option_strike'] >= v['price']):
            return 0
        else: 
            return float( v['price'] - v['option_strike'] )
    else: 
        if (v['option_right'] == 'PUT' ):  
            if ( v['option_strike'] <= v['price']):
                return 0
            else: 
                return float( v['option_strike'] - v['price']  ) 

def getExtrinseco(v): 
    # print(v['ask'], type(v['ask']),v) 
    return  float( ( float(v['ask']) + float(v['bid'])   )/2.0 ) - v['intrinseco']

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

# establish connection to the MetaTrader 5 terminal
def initMT5():
    if not mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password']):
        print("initialize() failed, error code =",mt5.last_error())
        quit()


# exibimos dads sobre o pacote MetaTrader5
print("MetaTrader5 package author: ",mt5.__author__)
print("MetaTrader5 package version: ",mt5.__version__)
 
# estabelecemos a conexão com o terminal MetaTrader 5 para a conta especificada
# initMT5()
 
# imprimimos informações sobre o estado da conexão, o nome do servidor e a conta de negociação
# print(mt5.terminal_info())
# imprimimos informações sobre a versão do MetaTrader 5
# print(mt5.version())


if __name__ == '__main__':
    timeNow = datetime.now().hour

    # print("run ",mt5.version())

    send_to_telegram("Robô procurando oportunidades!")    
   
    # ITSA4 BBAS3 ITUB4 ABEV3 B3SA3 JBSS3 VALE3 BOVA11 CSNA3 GGBR4 IRBR3 COGN3 BRFS3 LREN3 PRIO3 KLBN11 
    # RANI3 BBSE3 BRKM5 CYRE3 TAEE11 SANB11 GOAU4 CSAN3 WEGE3 NTCO3 CIEL3 HYPE3 HAPV3 PETZ3 VBBR3
    acoes = [ 'MRFG3','BBDC4', 'CPLE6','VIIA3', 'USIM5', 'MGLU3']
            
            
              
    for ac in acoes:
        try:
            initMT5()
            selected=mt5.symbol_select(ac,True)
            if not selected:
                print("Failed to select :: ",mt5.last_error())
                mt5.shutdown()
                quit()
            send_to_telegram("procurando oportunidades em "+ac)
            result = getInfoOpcoes(ac[0:4]+'A')
            
            res = getInfoOpcoes(ac[0:4]+'M')
            if (not res.empty):
                frames = [result, res]
                result = pd.concat(frames)
            
            for lt in letras:           
                # print(ac[0:4]+lt[0] )
                res = getInfoOpcoes(ac[0:4]+lt[0])
                if (not res.empty):
                    frames = [result, res]
                    result = pd.concat(frames)
                    
                # time.sleep(1) 
        
                # print(ac[0:4]+lt[1] )
                res = getInfoOpcoes(ac[0:4]+lt[1])
                if (not res.empty):
                    frames = [result, res]
                    result = pd.concat(frames)
                
                gc.collect()    
                
            # print(len(result))
            # print(result.head(3))
            # print(result.tail(3))
            getSBTH( result )
            
            selected=mt5.symbol_select(ac,False)
            result = []
            send_to_telegram("fim da procura em "+ac)  
            time.sleep(2) 
            mt5.shutdown()
            gc.collect()
            time.sleep(5) 
            
        except Exception:
            send_to_telegram("Erro na procura!")
            traceback.print_exc()
  
  
  
    # with concurrent.futures.ThreadPoolExecutor() as executor:
    #     futures = []
    #     for ac in acoes:
    #         futures.append(executor.submit(getInfoOpcoes, ativo=ac))
    #     for future in concurrent.futures.as_completed(futures):
    #         print(future.result())
    #         # vSBTH = getSBTH( future.result() )
    #         # vTERFCurta = getTerfCurta( future.result() )
    # vSBTH = getBox3Pontas( future.result() )
    #         # if (ac == 'PETR'):
    #         #     vTERFLonga = getTerfLonga( future.result() )
    #         # vJL = getJadedLizard( future.result() )  
    #         # vTH = getTaxaHedge( future.result() )  
    #         # vNTS = getNTS( future.result() ) 
    
    # with concurrent.futures.ThreadPoolExecutor() as exe:
    #     exe.submit(getInfoOpcoes, 2) 
    #     result = exe.map(getInfoOpcoes, acoes)
    # df = pd.DataFrame(result) #cria um dataframe com todos os values retornados do tick a tick


    print("--- %s seconds ---" % (time.time() - timeNow))
    timeNow = datetime.now().hour
    
    send_to_telegram("Fim da procura!")
    
    

