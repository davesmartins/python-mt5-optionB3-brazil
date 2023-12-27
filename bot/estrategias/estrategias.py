from datetime import datetime, timedelta
import pandas as pd
import MetaTrader5 as mt5
import logging
import time
import math 
import re
import yfinance as yf
import requests
import numpy as np
from scipy.stats import norm
import py_vollib.black_scholes as bs
from dateutil.relativedelta import relativedelta
import hashlib



from library import library

# from library import ACOES, getDataConfig, log, sendMessageGrupos

# Configurar o MetaTrader 5
def connectMT5(): 
    if not mt5.initialize(login=library.getDataConfig()['mt5']['account'], server=library.getDataConfig()['mt5']['server'],password=library.getDataConfig()['mt5']['password']):
        # Caso não esteja conectado, realizar a conexão automaticamente       
        # if not mt5.initialize(login=library.getDataConfig()['mt5']['account'], server=library.getDataConfig()['mt5']['server'],password=library.getDataConfig()['mt5']['password']):
        library.log.info("Não foi possível conectar ao MetaTrader 5.")
        library.log.info(library.getDataConfig()['mt5'] )
        library.log.info("initialize() failed, error code =",mt5.last_error())
        quit()
    else:
        library.log.info("MetaTrader 5 conectado.")        

def MT5Initialize() -> None:
    """inicializando o bot."""
    # mt5.shutdown()
    library.log.info("Conectando ao MetaTrader 5...")
    connectMT5()
    # mt5.initialize()
    
def finalizeMT5() -> None:
    """inicializando o bot."""
    library.log.info("finalizando o MetaTrader 5...")
    mt5.shutdown()

def getTick(codAtivo):
    idx = 0
    while True:
        tick = mt5.symbol_info_tick(codAtivo)
        if (tick.time != 0) or (idx>=10):
            return tick
        idx+=1

def getTickAlways(codAtivo):
    while True:
        tick = mt5.symbol_info_tick(codAtivo)
        if (tick.time != 0):
            return tick
            
def calculate_theoretical_option_price(option_type, spot_price, strike_price, time_to_maturity, interest_rate, volatility):
    return bs.black_scholes(option_type, spot_price, strike_price, time_to_maturity, interest_rate, volatility)
    

def getOptionsComDesvioPadrao(codigo_acao):
    mt5.symbol_select(codigo_acao, True)
    time.sleep(0.5) 
    print(codigo_acao)

    papel = getTickAlways(codigo_acao)
    # print(papel)
    spot_price = papel.last
    print(spot_price)
    
    listOp = mt5.symbols_get(codigo_acao[0:4])
    listOpF = filter(lambda s: s.basis == codigo_acao  and validar_codigo_opcao(s.name) , listOp)
    filtered_list = sorted(list(listOpF), key=lambda s: s.option_strike)
    
    max_expiration_date = datetime.now() + relativedelta(months=3) # timedelta(days=3 * 30)    
    
    library.GANHO_ESPERADO[ data_vencimento( datetime.now() ).strftime('%d/%m/%Y') ] = taxa_selic( ( datetime.now() ) )
    library.GANHO_ESPERADO[ data_vencimento( datetime.now() + relativedelta(months=1) ).strftime('%d/%m/%Y') ] = taxa_selic( ( datetime.now() + relativedelta(months=1) )  ) 
    library.GANHO_ESPERADO[ data_vencimento( datetime.now() + relativedelta(months=2) ).strftime('%d/%m/%Y') ] = taxa_selic( ( datetime.now() + relativedelta(months=2) )  ) 
    
    # print( library.GANHO_ESPERADO )
    
    std_dev = desvio_padrao_acao(codigo_acao)
    desvios_acima = spot_price + ((2.5) * std_dev)
    desvios_abaixo = spot_price - (1 * std_dev)
    print(std_dev, desvios_acima,  desvios_abaixo)
     
    filtered_options = []

    # Filtra as opções dentro de 2 desvios padrões do preço spot e até 3 meses do vencimento
    for op in filtered_list:
        expiration_date = datetime.fromtimestamp(op.expiration_time)
        if expiration_date >= datetime.now() and expiration_date <= max_expiration_date and ( op.option_strike >= desvios_abaixo)  and ( op.option_strike <= desvios_acima):
            mt5.symbol_select(op.name, True)
            # time.sleep(0.3)
            # print("ok")
            filtered_options.append( {
                'tick': op.name,
                'strike': op.option_strike,
                'lastUpdate': datetime.now()
            })
            
    time.sleep(0.5)  
    lista = []   
    for tk in (filtered_options):
        op = mt5.symbol_info(tk['tick'])
        # print(tk['tick'])
        preco =  getTick(tk['tick'])
        # library.log.info(op)
        # print(preco)
        # teorico = calculate_theoretical_option_price('c' if op.option_right == mt5.SYMBOL_OPTION_RIGHT_CALL else ('p' if op.option_right == mt5.SYMBOL_OPTION_RIGHT_PUT else '-'), 
        #                                                  papel.last, op.option_strike,
        #                                                  (pd.to_datetime(op.expiration_time, unit='s', errors='coerce') - datetime.now()).days / 365.25, 
        #                                                 11.75/12, vol_historica(codigo_acao))
        intrinseco = max(papel.last - op.option_strike, 0) if op.option_right == mt5.SYMBOL_OPTION_RIGHT_CALL else max(op.option_strike - papel.last, 0)
        extrinseco = ( preco.last - intrinseco)
        # extrinseco = ( (teorico if preco.last == 0 else preco.last) - intrinseco)
        lista.append( {
            'name': op.name,
            'basis': op.basis,
            'expiration_time':  pd.to_datetime(op.expiration_time, unit='s', errors='coerce'),
            'vencimento':  pd.to_datetime(op.expiration_time, unit='s', errors='coerce').to_pydatetime().strftime('%d/%m/%Y') ,
            'option_strike': op.option_strike,
            'bid': preco.bid,
            'ask': preco.ask,
            'last': preco.last,
            'letraVenc': op.name[4:5],
            'volume': preco.volume,
            'time_tick': preco.time_msc,
            'option_right': 'CALL' if op.option_right == mt5.SYMBOL_OPTION_RIGHT_CALL else ('PUT' if op.option_right == mt5.SYMBOL_OPTION_RIGHT_PUT else '-'),
            'option_mode': 'EUROPEIA' if op.option_mode == mt5.SYMBOL_OPTION_MODE_EUROPEAN else ('AMERICANA' if op.option_mode == mt5.SYMBOL_OPTION_MODE_AMERICAN else '-'),
            'intrinseco': intrinseco,
            'extrinseco': extrinseco,
            'precoPapel': papel.last
            # 'bs': teorico
                
        
        } )
        
    # print(lista)   
    
    lista1 = pd.DataFrame(lista )
        
    if not lista1.empty:
        # lista1['expiration_time'] = pd.to_datetime(lista1['expiration_time'], unit='s', errors='coerce')
        # lista1['time_tick'] = pd.to_datetime(lista1['time_tick'], unit='s', errors='coerce')
        lista1 = lista1.sort_values(by=['expiration_time', 'option_strike'])
 
    print(f" {lista1.size} options"  )    
    # print( f" {lista1['name']} - {lista1['basis']}- {lista1['option_right']}")    
        
    # library.ACOES_OP[codigo_acao] = []
    
    library.ACOES_OP[codigo_acao] = {
            'ativo': codigo_acao,
            'lastUpdate': datetime.now(),
            'vol_hist': vol_historica(codigo_acao),
            'opcoesCall':  lista1.loc[lista1['option_right'] == 'CALL'] ,
            'opcoesPut' :  lista1.loc[lista1['option_right'] == 'PUT']
        } 

    # print(f" {library.ACOES_OP[codigo_acao]['opcoesCall'].size} opções de CALL"  )  
    # print(f" {library.ACOES_OP[codigo_acao]['opcoesPut'].size} opções de PUt"  )  

    # print(lista1.head(10))
    return lista1


def validar_codigo_opcao(codigo):
    padrao = re.compile(r'^[A-Z;0-9]{4}[A-X]\d+$')
    # padrao = re.compile(r'^[A-Z]{4}[A-L][0-9]{2}[CP][0-9]\d+$')
    # print(codigo, bool(padrao.match(codigo)))
    return bool(padrao.match(codigo))

def desvio_padrao_acao(codigo_acao):

    # Obtém o histórico de preços da ação
    historico = mt5.copy_rates_from_pos(codigo_acao, mt5.TIMEFRAME_D1, 0, 366)
    
    df = pd.DataFrame(historico)
    # df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # preco_medio = df['close'].mean()    
    desvio_padrao = df['close'].std()
    
    # Calcula dois desvios padrão acima e abaixo do preço médio
    # dois_desvios_acima = preco_medio + 1 * desvio_padrao
    # dois_desvios_abaixo = preco_medio - 1 * desvio_padrao
    
    # # Exibe os resultados
    # print(f"Preço médio: {preco_medio}")
    # print(f"Desvio padrão: {desvio_padrao}")
    # print(f"desvios padrão acima: {dois_desvios_acima}")
    # print(f"desvios padrão abaixo: {dois_desvios_abaixo}")
    
    return desvio_padrao


def vol_historica(codigo_acao):
    start_date = datetime.now() - timedelta(days=360)
    end_date = datetime.now()

    rates = mt5.copy_rates_range(codigo_acao, mt5.TIMEFRAME_D1, start_date, end_date)

    data = pd.DataFrame(rates)

    # Calcular os retornos diários
    data['Log_Ret'] = data['close'].pct_change().apply(lambda x: math.log(1 + x))

    # Calcular a volatilidade histórica (anualizada)
    volatility = data['Log_Ret'].std() * math.sqrt(252)
 
    return volatility


def removeOptions(ac):
    listOp=mt5.symbols_get( ac[0:4] )   
    filtered_options = filter(lambda s: s.basis == ac or s.name == ac, listOp)    
    filtered_list = list(filtered_options)
    for s in filtered_list:
        try:
            selected=mt5.symbol_select(s.name,False)
        except Exception:
            print('ERRO DesSelect Ativo')         


def taxa_selic(dt):    
    
    diferenca_em_dias = (data_vencimento( dt ) - datetime.now()).days
    hoje = datetime.now().strftime('%d/%m/%Y')
    # print(datetime.now())
    # print(data_vencimento(datetime.now()).strftime('%d/%m/%Y') )
    # print(diferenca_em_dias)
    # print(hoje)
    url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial={hoje}&dataFinal={hoje}'

    # Fazendo a requisição à API do Bacen
    response = requests.get(url)

    # Verificando se a requisição foi bem-sucedida
    if response.status_code == 200:
        # Convertendo os dados para um DataFrame do pandas
        dados = response.json()
        df = pd.DataFrame(dados)

        # Convertendo as colunas relevantes para tipos numéricos
        df['valor'] = pd.to_numeric(df['valor'], errors='coerce')
        df['data'] = pd.to_datetime(df['data'], dayfirst=True)

        # Filtrando as colunas necessárias
        df = df[['data', 'valor']].dropna()

        # Extraindo a taxa Selic média no período
        taxa_selic_media = df['valor'].mean()
        
        # print(taxa_selic_media)

        return taxa_selic_media * diferenca_em_dias
    else:
        print(f"Erro na requisição. Código de status: {response.status_code}")
        return None


def taxa_cdi():
    # URL da API do Banco Central do Brasil para obter a taxa Selic (que é semelhante à CDI)
    url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json"

    try:
        # Faz uma solicitação à API
        resposta = requests.get(url)

        # Verifica se a solicitação foi bem-sucedida (código de status 200)
        if resposta.status_code == 200:
            # Obtém os dados JSON da resposta
            dados = resposta.json()

            # A taxa CDI geralmente é a última entrada nos dados
            taxa_cdi = dados[-1]['valor']

            return taxa_cdi
        else:
            print(f"Erro na solicitação. Código de status: {resposta.status_code}")
    except Exception as e:
        print(f"Erro ao obter a taxa CDI: {e}")

    return None

def data_vencimento(data_referencia):    
    primeiro_dia_mes = datetime(data_referencia.year, data_referencia.month, 1)
    
    # Encontrar o dia da semana do primeiro dia do mês (segunda é 0 e domingo é 6)
    dia_da_semana = primeiro_dia_mes.weekday()
    
    # Calcular o número de dias necessários para alcançar a primeira sexta-feira
    dias_ate_primeira_sexta = (4 - dia_da_semana + 7) % 7
    
    # Encontrar a primeira sexta-feira
    primeira_sexta = primeiro_dia_mes + timedelta(days=dias_ate_primeira_sexta)
    
    # Adicionar duas semanas para chegar à terceira sexta-feira
    terceira_sexta = primeira_sexta + timedelta(weeks=2)
    
    if (data_referencia > terceira_sexta):
        mes = 1 if (data_referencia.month == 12) else data_referencia.month+1
        ano = data_referencia.year+1 if (data_referencia.month == 12) else data_referencia.year
        return data_vencimento( datetime(ano, mes , 1) )    
    
    return terceira_sexta

                
def getPrecoAtivo(codigo_acao):
    try:
        print(codigo_acao)
        rates = mt5.copy_rates_from(codigo_acao, estrategias.mt5.TIMEFRAME_M1, datetime.now(), 1)  
        print(rates)
        if (rates is None):
            return -1
        
        return rates[0].close
    except Exception as e:
        print(f'Ocorreu um erro: {str(e)}')

# Atualizar preço opções

async def update_prices():
    # print(f"atualizando price")
    # start_time = time.time()
    for ac in library.getAtivos():
        # print(f"atualizando price de {ac} {library.ACOES_OP[ac]['lastUpdate'].strftime('%d/%m/%Y %H:%M:%S') }")
        library.ACOES_OP[ac]['lastUpdate'] = datetime.now()
        preco =  getTickAlways(ac)
        listaCall = library.ACOES_OP[ac]['opcoesCall'].copy()
        listaPut = library.ACOES_OP[ac]['opcoesPut'].copy()
        listaCall['precoPapel'] = preco.last
        listaPut['precoPapel'] = preco.last
        library.ACOES_OP[ac]['opcoesCall'] = await update( listaCall )
        library.ACOES_OP[ac]['opcoesPut'] = await update( listaPut )        
        # print( library.ACOES_OP[ac]  )
    
    # end_time = time.time()
    # # library.buscaGrupo()
    # library.printTime(start_time, end_time,"update_prices")    
        
async def update(lista):  
    for index, row in lista.iterrows():
        # print(f"Index: {index}, Name: {row['name']}, Strike: {row['option_strike']}, last: {row['last']}")
        op =  getTick(row['name'])
        
        # lista.at[index, 'Age'] = 31
        lista.at[index, 'bid'] = op.bid
        lista.at[index, 'ask'] = op.ask
        lista.at[index, 'last'] = op.last
        lista.at[index, 'volume'] = op.volume
        lista.at[index, 'time_tick'] = op.time_msc
        lista.at[index, 'intrinseco'] = max(row['precoPapel'] - row['option_strike'], 0) if row['option_right'] == 'CALL' else max(row['option_strike'] - row['precoPapel'] , 0)
        lista.at[index, 'extrinseco'] = ( row['last'] - row['intrinseco'])
        
    return  lista  
 
  
# procurar enradas box comprado 
 
async def search_box3Pontas():
    # start_time = time.time()
    for ac in library.getAtivos():
        # print(f"procurando Box 3 Pontas Comprado em {ac}") 
        listaCall = library.ACOES_OP[ac]['opcoesCall'].copy()
        listaPut = library.ACOES_OP[ac]['opcoesPut'].copy()        
        await Box3Pontas( listaCall, listaPut )
        
    # end_time = time.time()
    # # print(f"Box 3 Pontas Comprado ::") 
    # library.printTime(start_time, end_time, "search_box3Pontas") 
 
respBox3Pontas = """
••••••••••••••••••••••••••••••••••••••••••••••••
 BOX 3 PONTAS COMPRADO - (Zero Risco)
••••••••••••••••••••••••••••••••••••••••••••••••
Ativo: {ativo}
Vencimento: 🗓 {venc} - {dias} dias
Montagem : 💵 R$ {valor} 
Ganho:
  {percGanho}% - R$ {ganho}  
Selic {dias} dias: {selicPeriodo}%

🅲 {ativo}   R$ {cot} - {qtde}(qtd)

🅲 {oprC}  R$ {strikeC} - {qtde}(qtd)
    Últ. {lastC} Bid {bidC} Ask {askC}  
    Percentual acima do papel {percAcimaC}%  
    
🆅 {oprV}  R$ {strikeV} - {qtde}(qtd)
    Últ. {lastV} Bid {bidV} Ask {askV}  
    Percentual acima do papel {percAcimaV}%     
    
✳️ Delta Estrutural R$ {delt}       

"""        
 
async def Box3Pontas (call_list, put_list):    
    param = library.getOperacao('box3PontasComprado')
    for index, call in call_list.iterrows():
        
        if (call['option_strike'] >= call['precoPapel']):
            
            put_condition = (put_list['option_strike'] == call['option_strike']) & (put_list['expiration_time'] == call['expiration_time'])
            put = put_list[put_condition]
            put = put.iloc[0]
        
            idx = 'Box3PontasComprado#'+ put['basis']+"#"+put['name']+"#"+call['name']
            hash_md5 = hashlib.md5(idx.encode()).hexdigest()
            
            if (hash_md5 in library.OP_SALVAS):
                break
            
            # put = put_list.loc[put_list['option_strike'] == call['option_strike'] and put_list['expiration_time'] == call['expiration_time'] ]
            
            precoOperacao = ( ( call['precoPapel'] + put['last'] - call["last"] ) )
            diffInt = (call['option_strike'] - precoOperacao )
            ganho = ((diffInt )/( precoOperacao ))            
                                          
                        
            if valida_box3PontasComprado( put, call ):
                # print("Box de 3 pontas encontrado:")
                # print("Call Option:", call)
                # print("Put Option:", put)
                
                # library.OP_SALVAS[hash_md5] = {'operacao':'Box3PontasComprado', 'put': put, 'call': call}
                library.OP_SALVAS[hash_md5] = {'operacao':'Box3PontasComprado', 'ativo': put['basis'], 'ganho': "{:,.2f}".format( ganho * param["qtde"] ), 'put': put, 'call': call}
                
                diferenca_em_dias = (call['expiration_time'].to_pydatetime() - datetime.now()).days
                perAc = (( call['option_strike'] - call['precoPapel'])/ call['precoPapel'])*100
                delta = call['option_strike'] - call['precoPapel']
                
                msg = respBox3Pontas.format(
                    ativo=call['basis'],
                    venc= call['expiration_time'].to_pydatetime().strftime('%d/%m/%Y') ,
                    dias= diferenca_em_dias ,
                    valor="{:,.2f}".format( precoOperacao * param["qtde"] ),
                    percGanho="{:,.2f}".format( ganho * param["qtde"]),
                    ganho="{:,.2f}".format( (diffInt) * param["qtde"] ),
                    selicPeriodo = "{:,.2f}".format( library.GANHO_ESPERADO[  call['expiration_time'].to_pydatetime().strftime('%d/%m/%Y')  ] ),
                    cot="{:,.2f}".format( call['precoPapel'] ),
                    qtde=param["qtde"],
                    oprC= put["name"],
                    strikeC="{:,.2f}".format( put["option_strike"] ),
                    lastC="{:,.2f}".format( put["last"] ),
                    bidC="{:,.2f}".format( put["bid"] ),
                    askC="{:,.2f}".format( put["ask"] ),
                    percAcimaC="{:,.2f}".format( perAc ),
                    oprV= call["name"],
                    strikeV="{:,.2f}".format( call["option_strike"] ),
                    lastV="{:,.2f}".format( call["last"] ),
                    bidV="{:,.2f}".format( call["bid"] ),
                    askV="{:,.2f}".format( call["ask"] ),
                    percAcimaV="{:,.2f}".format( perAc ),
                    delt="{:,.2f}".format(delta),
                ) 
                
                library.sendMessageAllGroup(msg) 
           
def valida_box3PontasComprado( put, call ):
    
    precoOperacao = ( ( call['precoPapel'] + put['last'] - call["last"] ) )
    diffInt = (call['option_strike'] - precoOperacao )
    ganho = ((diffInt )/( precoOperacao ))  
            
    return (ganho > library.GANHO_ESPERADO[  call['expiration_time'].to_pydatetime().strftime('%d/%m/%Y')  ]) and (( call['ask'] >= call['last'] >= call['bid'] ) and (call['ask'] > 0) and (call['bid'] > 0)) and (( put['ask'] >= put['last'] >= put['bid'] ) and (put['ask'] > 0) and (put['bid'] > 0))
                

# procurar enradas SBTH 
 
async def search_SBTH():
    # start_time = time.time()
    for ac in library.getAtivos():
        # print(f"procurando SBTH em {ac}") 
        listaCall = library.ACOES_OP[ac]['opcoesCall'].copy()
        listaPut = library.ACOES_OP[ac]['opcoesPut'].copy()        
        await SBTH( listaCall, listaPut )
        
    # end_time = time.time()
    # # print(f"SBTH ::") 
    # library.printTime(start_time, end_time, "search_SBTH") 
 
respSBTH = """
••••••••••••••••••••••••••••••••••••••••••••••••
 SBTH - (Zero Risco)
••••••••••••••••••••••••••••••••••••••••••••••••
Ativo: {ativo}
Vencimento: 🗓 {venc} - {dias} dias
Montagem : 💵 R$ {valor} 
Ganho:
  {percGanho}% - R$ {ganho}  
Selic {dias} dias: {selicPeriodo}%

🅲 {ativo}   R$ {cot} - {qtde}(qtd)

🅲 {oprC}  R$ {strikeC} - {qtde}(qtd)
    Últ. {lastC} Bid {bidC} Ask {askC}  
    Percentual acima do papel {percAcimaC}%  
    
✳️ Delta Estrutural R$ {delt}       

"""        
 
async def SBTH (call_list, put_list):    
    param = library.getOperacao('SBTH')
    for index, put in put_list.iterrows():
        
        if (put['option_strike'] >= put['precoPapel']):
        
            # put_condition = (put_list['option_strike'] == call['option_strike']) & (put_list['expiration_time'] == call['expiration_time'])
            # put = put_list[put_condition]
            # put = put.iloc[0]
            
            # put = put_list.loc[put_list['option_strike'] == call['option_strike'] and put_list['expiration_time'] == call['expiration_time'] ]
            
            idx = 'SBTH#'+ put['basis']+"#"+put['name']
            hash_md5 = hashlib.md5(idx.encode()).hexdigest()
            
            if (hash_md5 in library.OP_SALVAS):
                break
            
            precoOperacao = ( ( put['precoPapel'] + put['last'] ) )
            diffInt = (put['option_strike'] - precoOperacao )
            ganho = ((diffInt )/( precoOperacao ))                                          
                        
            if valida_SBTH( put ):
                # print("SBTH:")
                # print("Ativo:", put['basis'], put['precoPapel'])
                # print("Put Option:", put)                
                
                library.OP_SALVAS[hash_md5] = {'operacao':'SBTH', 'ativo': put['basis'], 'ganho': "{:,.2f}".format( ganho * param["qtde"] ), 'put': put}
                
                diferenca_em_dias = (put['expiration_time'].to_pydatetime() - datetime.now()).days
                perAc = (( put['option_strike'] - put['precoPapel'])/ put['precoPapel'])*100
                delta = put['option_strike'] - put['precoPapel']
                
                msg = respSBTH.format(
                    ativo=put['basis'],
                    venc= put['expiration_time'].to_pydatetime().strftime('%d/%m/%Y') ,
                    dias= diferenca_em_dias ,
                    valor="{:,.2f}".format( precoOperacao * param["qtde"] ),
                    percGanho="{:,.2f}".format( ganho * param["qtde"] ),
                    ganho="{:,.2f}".format( (diffInt * param["qtde"]) ),
                    selicPeriodo = "{:,.2f}".format( library.GANHO_ESPERADO[  put['expiration_time'].to_pydatetime().strftime('%d/%m/%Y')  ] ),
                    cot="{:,.2f}".format( put['precoPapel'] ),
                    qtde=param["qtde"],
                    oprC= put["name"],
                    strikeC="{:,.2f}".format( put["option_strike"] ),
                    lastC="{:,.2f}".format( put["last"] ),
                    bidC="{:,.2f}".format( put["bid"] ),
                    askC="{:,.2f}".format( put["ask"] ),
                    percAcimaC="{:,.2f}".format( perAc ),
                    delt="{:,.2f}".format(delta),
                ) 
                
                library.sendMessageAllGroup(msg)  
  
def valida_SBTH( put ):
    param = library.getOperacao('SBTH')
    precoOperacao = ( ( put['precoPapel'] + put['last'] ) )
    diffInt = (put['option_strike'] - precoOperacao )
    ganho = ((diffInt )/( precoOperacao )) 
    return ( diffInt >= param["ganho"] ) and ( put['ask'] >= put['last'] >= put['bid'] ) and (put['ask'] > 0) and (put['bid'] > 0)    
 
def verificaOperacao():
    op = []
    key = []
    for chave, opcao in library.OP_SALVAS.items():
        if (opcao["operacao"] == 'SBTH'):
            if ( valida_SBTH( opcao["put"] ) ):
                op.append( f'ID: {chave} : Ativo: {opcao["ativo"]}, operação: {opcao["operacao"]}, ganho: {opcao["ganho"]}' )
            else:
                key.append(chave)    
                
        if (opcao["operacao"] == 'box3PontasComprado'):
            if ( valida_box3PontasComprado( opcao["put"], opcao["call"] ) ):
                op.append( f'{opcao["operacao"]} :: Ativo: {opcao["ativo"]}, ganho: {opcao["ganho"]}' )
            else:
                key.append(chave)  
        
    for k in key:
        del library.OP_SALVAS[k]           
                
    return op            
            
        
 
# name
# basis
# expiration_time
# option_strike
# bid
# ask
# last
# letraVenc
# volume
# time_tick
# option_right
# option_mode
# intrinseco
# extrinseco
# precoPapel 