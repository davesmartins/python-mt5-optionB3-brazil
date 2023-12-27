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

letras = [['A','M'],['B','N'],['C','O'],['D','P'],['E','Q'],['F','R'],['G','S'],['H','T'],['I','U'],['J','V'],['K','W'],['L','X']]
# letras = [['B','N'],['C','O'],['D','P'],['E','Q'],['F','R'],['G','S'],['H','T'],['I','U'],['J','V'],['K','W'],['L','X']]

def getInfoOpcoes(acao, ativo, preco):    
    try:        
        symbols=mt5.symbols_get( ativo )
        df = converter(symbols)
        print(ativo, len(df))
        if (len(df) <= 0):
            return pd.DataFrame([],
                        columns=['expiration_time', 'option_mode', 'option_right', 'option_strike',
                                 'basis', 'description', 'name', 'letraVenc', 'mesVenc', 'price', 'bid', 
                                 'ask', 'last', 'intrinseco', 'extrinseco', 'volume', 'time_tick', 'vencimento']) 
         
        df.drop(["custom","chart_mode","select","visible","session_deals","session_buy_orders","session_sell_orders","volume","volumehigh","volumelow","time","digits","spread","spread_floa","ticks_bookdepth",
                "trade_calc_mode","trade_mode","start_time","trade_stops_level","trade_freeze_level","trade_exemode","swap_mode","swap_rollover3days","margin_hedged_use_leg","expiration_mode",
                "filling_mode","order_mode","order_gtc_mode","bid","bidhigh","bidlow","ask","askhigh","asklow","last","lasthigh","lastlow","volume_real","volumehigh_real","volumelow_real",
                "point","trade_tick_value","trade_tick_value_profit","trade_tick_value_loss","trade_tick_size","trade_contract_size","trade_accrued_interest","trade_face_value","trade_liquidity_rate",
                "volume_min","volume_max","volume_step","volume_limit","swap_long","swap_short","margin_initial","margin_maintenance","session_volume","session_turnover","session_interest","session_buy_orders_volume",
                "session_sell_orders_volume","session_open","session_close","session_aw","session_price_settlement","session_price_limit_min","session_price_limit_max","margin_hedged","price_change","price_volatility",
                "price_theoretical","price_greeks_delta","price_greeks_theta","price_greeks_gamma","price_greeks_vega","price_greeks_rho","price_greeks_omega","price_sensitivity","category","currency_base",
                "currency_profit","currency_margin","bank","formula","isin","page", "path", "exchange"],
                            axis=1, inplace=True)
        
        df['letraVenc']=""
        df['mesVenc']=""
        df['price']=0
        df['bid']=0
        df['ask']=0
        df['last']=0
        df['intrinseco']=0
        df['extrinseco']=0
        df['volume']=0
        df['time_tick'] = ''
        df['vencimento'] = ''
        
        df = df.query(f"(option_strike > 0) and (basis == '{acao}')", engine='python')       
        
        df.set_index("name", inplace=True) 
    
        # print("--> ", len(df), df)
        for idx in df.index:
            # selected=mt5.symbol_select(idx,True)
            # if not selected:
            #     print("Failed to select Option :: ",mt5.last_error())
            #     mt5.shutdown()
            #     quit()    
            # time.sleep(0.3)        
            df['expiration_time'][idx] = pd.to_datetime(df['expiration_time'][idx], unit="s")
            # print("--> ", len(df))
            # df['option_strike'] = df['option_strike'].astype(float)   
            
            # print("--> ", df['name'][idx], type(df['name'][idx]))
            df['letraVenc'][idx] = idx[4:5]
            df['option_right'][idx] = table_call_put(df['option_right'][idx])  
            df['option_mode'][idx] = table_tipo(df['option_mode'][idx]) 
            df['mesVenc'][idx] =  table_mes(df['letraVenc'][idx])             
             
            # time.sleep(0.1)          
            lasttickOp = mt5.symbol_info_tick( idx ) 
            if (lasttickOp != 'NoneType'):
                try:        
                    df['price'][idx] = preco
                    df['bid'][idx] =  lasttickOp.bid 
                    df['ask'][idx] =  lasttickOp.ask
                    df['last'][idx] =  lasttickOp.last
                    df['intrinseco'][idx] =   getIntrinseco( df, idx )
                    df['extrinseco'][idx] =  getExtrinseco( df, idx )
                    df['volume'][idx] = lasttickOp.volume
                    df['time_tick'][idx] = pd.to_datetime(lasttickOp.time  , unit='s')  
                    df['vencimento'][idx] = pd.to_datetime(df['expiration_time'][idx], unit="s") #.dt.strftime("%d/%m/%Y") 
                except Exception:   
                    print(lasttickOp) 
            
            # print( df[idx])            
            selected=mt5.symbol_select( idx ,False)

        df = df.query('ask > 0 and bid > 0', engine='python')
        df = df.sort_values(['option_strike'],
              ascending = [True])
        
        print('-> ',ativo, len(df))
        # print(df.tail(1))
        return df 
    except Exception:
        traceback.print_exc()
        quit
        # return pd.DataFrame()
      
def getSelic(dt):
    selic = sgs.get({'selic':432}, start = dt ) #'2023-01-21')
    # print(type(selic) )
    return float(selic['selic'][0] )
    # return sgs.get({'selic':432}, start = '2023-01-20')

def converter(ativos):
    df = pd.DataFrame(ativos, 
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
    return df

def getSBTH(op):    
    resp = """
••••••••••••••••••••••••••••••••••••••••••••••••
 DISTORÇÃO
••••••••••••••••••••••••••••••••••••••••••••••••
Ativo: *{ativo}*         🗓 {venc}
Montagem : 💵 *R$ {valor}* 
Ganho :  {percGanho}%  R$ {ganho}  
Ganho mensal : {percGanhoM}%
+ {rol} rolagens
CDI {dias} dias : {cdiPeriodo}%
Selic anual: {selic}%

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
            try:
                d2 = opc['vencimento'][idx].strftime('%d/%m/%Y') # datetime.strptime(opc['vencimento'][idx], '%d/%m/%Y')
                vdias = abs(( opc['vencimento'][idx] - datetime.today() ).days)
                vMes = ((vdias-(vdias%30))/30)
                cdi = ((selic/360)* vdias)
            except Exception:
                print(' --> ', opc['vencimento'][idx] )
                print(' <-- ',idx)
                print(opc[:,idx] )
                traceback.print_exc()
                quit
            perAc = ((opc['option_strike'][idx] - opc['price'][idx])/ opc['price'][idx])*100
            
            send_to_telegram( resp.format(
                ativo=opc['basis'][idx],
                venc= d2 ,
                valor="{:,.2f}".format( precoCompra ),
                cot="{:,.2f}".format(opc['price'][idx]),
                opr= idx,
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
                selic=selic
            ) )

def getBox3Pontas(op):    
    resp = """
••••••••••••••••••••••••••••••••••••••••••••••••
 BOX 3 PONTAS - (Zero Risco)
••••••••••••••••••••••••••••••••••••••••••••••••
Ativo: *{ativo}*         🗓 {venc}
Montagem : 💵 R$ {valor} 
Ganho Travado :  {percGanho}%  R$ {ganho}  
Ganho mensal : {percGanhoM}%
CDI {dias} dias : {cdiPeriodo}%
Selic anual: {selic}%

🅲 {ativo}   R$ {cot} - {qtde}(qtd)

🅲 {oprC}  R$ {strikeC} - {qtde}(qtd)
    Últ. {lastC} Bid {bidC} Ask {askC}  
    Percentual acima do papel {percAcimaC}%  
    
🆅 {oprV}  R$ {strikeV} - {qtde}(qtd)
    Últ. {lastV} Bid {bidV} Ask {askV}  
    Percentual acima do papel {percAcimaV}%     
    
✳️ Delta Estrutural R$ {delt}       

"""
    if (len(op) == 0): return
    precoPapel = op.iloc[0]['price']
    value_to_check = datetime.today().replace(month=datetime.today().month+2)
    filter_mask = op['vencimento'] < value_to_check
    # filtered_df = df[filter_mask]
    opcP = op[ (  (op['option_strike'] >=precoPapel ) & ( filter_mask ) & (op['option_right'] == "PUT")  )  ]
    opcC = op[ (  (op['option_strike'] >=precoPapel ) & ( filter_mask ) & (op['option_right'] == "CALL")  )  ]
    
    tam = len(opcC) if (len(opcC) < len(opcP)) else len(opcP) 
    
    if (tam == 0): return
    
    for idx in range(tam):
        oc = opcC[ opcC['option_strike'] == opcP.iloc[idx]['option_strike']  ]
        if ( (len(oc) > 0) and (oc.iloc[0]['bid'] >= opcP.iloc[idx]['ask']) ):
            print("=================================")
            print('Comprar :: ', opcP.index[idx], opcP.iloc[idx]['option_strike'], opcP.iloc[idx]['price'], opcP.iloc[idx]['ask'] )
            print('Vender :: ', oc.index[0], oc.iloc[0]['option_strike'], oc.iloc[0]['price'], oc.iloc[0]['bid'] )
            print("=================================")
            
            precoCompra = ( ( precoPapel + opcP['ask'][idx] - oc.iloc[0]["bid"] ) * QTDE )
            delta = opcP["option_strike"][idx] - precoPapel
            diffInt = (opcP["option_strike"][idx] - precoCompra/100)
            ganho = ((diffInt )/( precoCompra / QTDE ))*100
            perAc = ((opcP['option_strike'][idx] - precoPapel)/ precoPapel)*100
            try:
                d2 = opcP['vencimento'][idx].strftime('%d/%m/%Y') # datetime.strptime(opc['vencimento'][idx], '%d/%m/%Y')
                vdias = abs(( opcP['vencimento'][idx] - datetime.today() ).days)
                vMes = ((vdias-(vdias%30))/30)
                cdi = ((selic/360)* vdias)
            except Exception:
                traceback.print_exc()
                quit
            
            send_to_telegram( resp.format(
                ativo=opcP['basis'][idx],
                venc= d2 ,
                valor="{:,.2f}".format( precoCompra ),
                percGanho="{:,.2f}".format( ganho ),
                ganho="{:,.2f}".format( (diffInt) * QTDE ),
                percGanhoM="{:,.2f}".format( ganho/(vMes+1) ),
                dias= vdias,
                cdiPeriodo = "{:,.2f}".format( cdi ),
                selic=selic,
                cot="{:,.2f}".format(opcP['price'][idx]),
                qtde=QTDE,
                oprC=opcP.index[idx],
                strikeC="{:,.2f}".format(opcP["option_strike"][idx]),
                lastC="{:,.2f}".format(opcP["last"][idx]),
                bidC="{:,.2f}".format(opcP["bid"][idx]),
                askC="{:,.2f}".format(opcP["ask"][idx]),
                percAcimaC="{:,.2f}".format( perAc ),
                oprV=oc.index[0],
                strikeV="{:,.2f}".format(oc["option_strike"][0]),
                lastV="{:,.2f}".format(oc["last"][0]),
                bidV="{:,.2f}".format(oc["bid"][0]),
                askV="{:,.2f}".format(oc["ask"][0]),
                percAcimaV="{:,.2f}".format( perAc ),
                delt="{:,.2f}".format(delta),
            ) )
    
def getTerfCurta(op):    
    resp = """
••••••••••••••••••••••••••••••••••••••••••••••••
 TERF - {tipoTerf}
••••••••••••••••••••••••••••••••••••••••••••••••
Ativo: *{ativo}*         🗓 {venc}
Montagem : 💵 R$ {valor} 
Falta pagar na call : R$ {ganhoA} ({percGanhoA}%)   
Falta pagar mensal  : R$ {percGanhoMA}  
Falta pagar na put  : R$ {ganhoB} ({percGanhoB}%)   
Falta pagar mensal  : R$ {percGanhoMB}  
+ {rol} rolagens
CDI {dias} dias : {cdiPeriodo}%
Selic anual: {selic}%

🅲 {ativo}   R$ {cot} - {qtde}(qtd)

🅲 {oprC}  R$ {strikeC} - {qtde}(qtd)
    Últ. {lastC} Bid {bidC} Ask {askC}  
    Percentual acima do papel {percAcimaC}%  
    
🆅 {oprV}  R$ {strikeV} - {qtde}(qtd)
    Últ. {lastV} Bid {bidV} Ask {askV}  
    Percentual acima do papel {percAcimaV}%     
    
✳️ Delta Estrutural na Call R$ {deltA}    
✳️ Delta Estrutural na Put  R$ {deltB}     

"""
   
    if (len(op) == 0): return
    precoPapel = op.iloc[0]['price']
    precoMinPut = precoPapel * (1.04)
    precoMaxPut = precoPapel * (1.09)
    precoMinCall = precoPapel * (1.04)
    precoMaxCall = precoPapel * (1.11)
    
    mesPut = datetime.today().replace(month=datetime.today().month+1,day=1)
    mesCall = datetime.today().replace(month=datetime.today().month+1,day=1)
    
    filter_mask_put = op['vencimento'] >= mesPut
    filter_mask_call = op['vencimento'] <= mesCall
    # filtered_df = df[filter_mask]
    opcP = op[ (  (op['option_strike'] >=precoMinPut ) & (op['option_strike'] <= precoMaxPut )  & ( filter_mask_put ) & (op['option_right'] == "PUT")  )  ]
    
    opcC = op[ (  (op['option_strike'] >=precoMinCall ) & (op['option_strike'] <= precoMaxCall )  & ( filter_mask_call ) & (op['option_right'] == "CALL")  )  ]
    
    # tam = len(opcC) if (len(opcC) < len(opcP)) else len(opcP) 
    
    if ( (len(opcP) == 0) or (len(opcC) == 0)): return
    
    for idx in range( len(opcP) ):
        
        deltaP = opcP.iloc[idx]["option_strike"] - precoPapel
        precoPut = opcP.iloc[idx]["ask"]
        
        dtVencimentoPut = opcP.iloc[idx]['vencimento'].strftime('%d/%m/%Y') 
        vdiasPut = abs(( opcP.iloc[idx]['vencimento'] - datetime.today() ).days)
        vMesPut = ((vdiasPut-(vdiasPut%30))/30)        
        
        for idx1 in range( len(opcC) ):
            
            deltaC = opcC.iloc[idx1]["option_strike"] - precoPapel
            precoCall = opcC.iloc[idx1]["bid"]
            
            precoMont = precoPapel + precoPut - precoCall
            
            faltaPagarPut = (deltaP + precoCall) - precoPut
            faltaPagarPutMes = faltaPagarPut/(vMesPut)
            faltaPagarCall = (deltaC + precoCall) - precoPut  
            faltaPagarCallMes = faltaPagarCall/(vMesPut)   
            
            if ((faltaPagarPutMes <= (precoCall*0.40*-1) ) | (faltaPagarCallMes <= (precoCall*0.40*-1) )):
                continue      
            
            if (opcC.iloc[idx1]["option_strike"] > opcP.iloc[idx]["option_strike"]):
               tf = 'Delta Positivo'
            else:
               if (opcC.iloc[idx1]["option_strike"] < opcP.iloc[idx]["option_strike"]):
                   tf = 'Delta Negativo'
               else: 
                   tf = 'Mesmo Strike'   
                   
            print("=================================")
            print('Comprar PUT :: ', opcP.index[idx], opcP.iloc[idx]['option_strike'], opcP.iloc[idx]['price'], opcP.iloc[idx]['ask'], faltaPagarPutMes )
            print('Vender CALL :: ', opcC.index[idx1], opcC.iloc[idx1]['option_strike'], opcC.iloc[idx1]['price'], opcC.iloc[idx1]['bid'], faltaPagarCallMes )
            print("=================================")        
            
            precoCompra = ( precoMont * QTDE )
            
            diffIntP = faltaPagarPut  # (opcP.iloc[idx]["option_strike"] - precoCompra/100)
            diffIntC = faltaPagarCall  #  (opcC.iloc[idx]["option_strike"] - precoCompra/100)
            ganhoP = ((diffIntP )/( precoMont ))*100
            ganhoC = ((diffIntC )/( precoMont ))*100
            perAcP = ((opcP.iloc[idx]['option_strike'] - precoPapel)/ precoPapel)*100
            perAcC = ((opcC.iloc[idx1]['option_strike'] - precoPapel)/ precoPapel)*100
            cdi = ((selic/360)* vdiasPut)
            
            send_to_telegram( resp.format(
                tipoTerf= tf,
                ativo=opcP.iloc[idx]['basis'],
                venc= dtVencimentoPut ,                
                valor="{:,.2f}".format( precoCompra ),                
                percGanhoA="{:,.2f}".format( ganhoC ),
                ganhoA="{:,.2f}".format( (diffIntC) * QTDE ),                
                percGanhoB="{:,.2f}".format( ganhoP ),
                ganhoB="{:,.2f}".format( (diffIntP) * QTDE ),            
                percGanhoMA="{:,.2f}".format( diffIntC/vMesPut) ,
                percGanhoMB="{:,.2f}".format( diffIntP/vMesPut) ,
                dias= vdiasPut,
                rol= "{:,.2f}".format(vMesPut),
                cdiPeriodo = "{:,.2f}".format( cdi ),
                selic=selic,
                cot="{:,.2f}".format(opcP.iloc[idx]['price']),
                qtde=QTDE,
                oprC=opcP.index[idx],
                strikeC="{:,.2f}".format(opcP.iloc[idx]["option_strike"]),
                lastC="{:,.2f}".format(opcP.iloc[idx]["last"]),
                bidC="{:,.2f}".format(opcP.iloc[idx]["bid"]),
                askC="{:,.2f}".format(opcP.iloc[idx]["ask"]),
                percAcimaC="{:,.2f}".format( perAcP ),
                oprV=opcC.index[idx1],
                strikeV="{:,.2f}".format(opcC.iloc[idx1]["option_strike"]),
                lastV="{:,.2f}".format(opcC.iloc[idx1]["last"]),
                bidV="{:,.2f}".format(opcC.iloc[idx1]["bid"]),
                askV="{:,.2f}".format(opcC.iloc[idx1]["ask"]),
                percAcimaV="{:,.2f}".format( perAcC ),
                deltA="{:,.2f}".format( deltaC),
                deltB="{:,.2f}".format( deltaP ),
            ) )
  
def getIntrinseco(v, idx): 
    if (v['option_right'][idx] == 'CALL' ):  
        if ( v['option_strike'][idx] >= v['price'][idx]):
            return 0
        else: 
            return float( v['price'][idx] - v['option_strike'][idx] )
    else: 
        if (v['option_right'][idx] == 'PUT' ):  
            if ( v['option_strike'][idx] <= v['price'][idx]):
                return 0
            else: 
                return float( v['option_strike'][idx] - v['price'][idx]  ) 

def getExtrinseco(v,idx): 
    # print(v['ask'], type(v['ask']),v) 
    return  float( ( float(v['ask'][idx]) + float(v['bid'][idx])   )/2.0 ) - v['intrinseco'][idx]

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
    
    selic = getSelic( datetime.today().strftime('%Y-%m-%d') )
    print(selic)
    initMT5()
   
    #               
    #   ,'VALE3', 'PRIO3', 'SUZB3', 'FLRY3', 'BPAC11', 'LREN3' 
    acoes = ['CPLE6', 'USIM5', 'PETR4','BBDC4', 'MRFG3', 'JBSS3', 'ITUB4', 'BBAS3', 'DXCO3',
             'SANB11', 'BBSE3', 'RANI3', 'BRKM5', 'KLBN11' ,'VIIA3', 'MGLU3', 'ITSA4', 'TIMS3', 
             'B3SA3', 'ABEV3', 'TRPL4', 'TAEE11', 'CMIG4', 'VBBR3', 'IRBR3', 'PETZ3', 'CIEL3', 
             'NTCO3', 'BRFS3', 'HYPE3', 'HAPV3', 'BOVA11', 'BBDC3', 'AMER3', 'SOMA3', 'WEGE3',
             'COGN3', 'YDUQ3', 'CYRE3', 'EZTC3', 'MRVE3', 'GGBR4', 'CSAN3', 'GOAU4', 'CSNA3', 'CMIN3', 
             'POSI3', 'BEEF3', 'ECOR3', 'ALPA4', 'AZUL4', 'CCRO3', 'QUAL3', 'RAIZ4', 'SAPR11', 'LWSA3'  ]            
              
    for ac in acoes:
        try:
            
            send_to_telegram("procurando oportunidades em "+ac)
            listOp=mt5.symbols_get( ac[0:4] )
            for s in listOp:  
                # print(ac, s.basis)              
                if (s.basis == ac or s.name == ac):
                    selected=mt5.symbol_select(s.name,True)
                    time.sleep(0.1) 
                    if not selected:
                        print("Failed to select :: ",mt5.last_error())
                        # mt5.shutdown()
                        quit()
            
            result = pd.DataFrame([],
                        columns=['expiration_time', 'option_mode', 'option_right', 'option_strike',
                                 'basis', 'description', 'name', 'letraVenc', 'mesVenc', 'price', 'bid', 
                                 'ask', 'last', 'intrinseco', 'extrinseco', 'volume', 'time_tick', 'vencimento'])            
            
            for lt in letras:           
                # print(ac[0:4]+lt[0] )
                lasttick=mt5.symbol_info_tick( ac )  
                # print(lasttick)
                res = getInfoOpcoes(ac, ac[0:4]+lt[0], lasttick.last)
                if (not res.empty):
                    frames = [result, res]
                    result = pd.concat(frames)
                            
                # print(ac[0:4]+lt[1] )
                res = getInfoOpcoes(ac, ac[0:4]+lt[1], lasttick.last)
                if (not res.empty):
                    frames = [result, res]
                    result = pd.concat(frames)
                
            # selected=mt5.symbol_select(ac,False)             
            
            print('tamanho :: ',len(result), ' strikes')
            # print(result.head(1))
            # print(result.tail(1))
            
            getSBTH( result )  
            getBox3Pontas( result )  
            getTerfCurta( result )   
            # getJadedLizard( result ) - 5% de distancia da put, 5% da trava, lucro de cdi na alta???? +- 50 dias       
            
            result = []
            send_to_telegram("fim da procura em "+ac) 
            
            for s in listOp:
                try:
                    selected=mt5.symbol_select(s.name,False)
                except Exception:
                    print('ERRO DesSelect Ativo')    
            
        except Exception:
            send_to_telegram("Erro na procura!")
            for s in listOp:
                try:
                    selected=mt5.symbol_select(s.name,False)
                except Exception:
                    print('ERRO DesSelect Ativo')  
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

    mt5.shutdown() 
    print("--- %s seconds ---" % pd.to_datetime(time.time() - timeNow, unit="s").strftime("%H:%M:%S") )
    timeNow = datetime.now().hour
    
    send_to_telegram("Fim da procura!")
    
    

