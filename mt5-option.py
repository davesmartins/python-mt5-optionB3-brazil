import pandas as pd
import concurrent.futures
import MetaTrader5 as mt5
import time
from datetime import datetime, timedelta
import json
from sqlalchemy import create_engine
import csv
from io import StringIO

with open("config.json") as json_data_file:
    data = json.load(json_data_file)

host = data['sql']['host']
dbname = data['sql']['db']
user = data['sql']['user']
password = data['sql']['password']
port = data['sql']['port']

engine = create_engine(
    f'postgresql://{user}:{password}@{host}:{port}/{dbname}')

def filtered_data():
    data = pd.read_csv('SI_D_SEDE.txt', sep="|", header=None, names=[
        "Empresa", "codBuySell", "buySell", '1', '2',
        'ativoCodigo', 'onPN', '4', '5', '6', '7', '8', 'codigoAtivo', 'codClasseOpcao',
        'classeOpcao', 'Strike', 'Date', '14']) #Colunas com numeros nāo sao dados relevantes ao meu ver
    data.drop(['1', '2', '4', '5', '6', '8', '7',
               '14', 'onPN'], axis=1, inplace=True)
    data.drop(3, inplace=True)  # Drop nas opçoes que nao sao de ações
    data['Date'] = pd.to_datetime(data['Date'], format='%Y%m%d')
    data.ativoCodigo = data.ativoCodigo.str.strip()
    listaIbov = pd.read_csv('IBX-lista.csv', sep=';')
    lst = listaIbov.index.str.replace('\d+', '')
    # filtra para somente os ativos IBX100
    data = data.query('ativoCodigo in @lst')
    dateFuture = datetime.now() + timedelta(days=90) #Filtra somente para retornar os proximos 90 dias
    data = data.loc[(data['Date'] >= datetime.now())
                    & (data['Date'] <= dateFuture)]
    data['Date'] = data['Date'].dt.strftime('%Y/%m/%d')
    data = data.to_numpy()
    return data

def dataMt5(array):
    ativo = array[4]
    selected = mt5.symbol_select(ativo, True)
    if not selected:
        print(f"Failed to select {ativo}")
        return ativo
    symbol_info_tick_dict = mt5.symbol_info_tick(ativo)._asdict()
    mt5.symbol_select(ativo, False)

    # Join no Dict para enviar para o dataframe
    symbol_info_tick_dict.pop("time")
    symbol_info_tick_dict.pop("time_msc")
    symbol_info_tick_dict.pop("flags")
    symbol_info_tick_dict['ativo'] = f"'{ativo}'"
    symbol_info_tick_dict['strike'] = array[7]
    symbol_info_tick_dict['vencimento'] = f"'{array[8]}'"
    symbol_info_tick_dict['tpo_opcao'] = array[1]
    symbol_info_tick_dict['classe_opcao'] = array[5]
    return symbol_info_tick_dict


def psql_insert_copy(table, conn, keys, data_iter): #insert no SQL usando o Copy
    dbapi_conn = conn.connection
    with dbapi_conn.cursor() as cur:
        s_buf = StringIO()
        writer = csv.writer(s_buf)
        writer.writerows(data_iter)
        s_buf.seek(0)
        columns = ', '.join('"{}"'.format(k) for k in keys)
        if table.schema:
            table_name = '{}.{}'.format(table.schema, table.name)
        else:
            table_name = table.name
        sql = 'COPY {} ({}) FROM STDIN WITH CSV'.format(
            table_name, columns)
        cur.copy_expert(sql=sql, file=s_buf)

mt5.shutdown()

# establish connection to the MetaTrader 5 terminal
if not mt5.initialize(login=data['mt5']['account'],
                      server=data['mt5']['password'], password=data['mt5']['server']):

    print("initialize() failed, error code =", mt5.last_error())
    quit()

data_Array = filtered_data()

if __name__ == '__main__':
    timeNow = datetime.now().hour

    while timeNow < 17: #executa continuamente ate o fechamento do mercado as 17:00
        result = []
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor() as exe:
            exe.submit(dataMt5, 10) 
            result = exe.map(dataMt5, data_Array)
        df = pd.DataFrame(result) #cria um dataframe com todos os values retornados do tick a tick
        df.to_sql('option_tick', engine,
                  method=psql_insert_copy, if_exists='replace')
        print("--- %s seconds ---" % (time.time() - start_time))
        timeNow = datetime.now().hour

mt5.shutdown()
