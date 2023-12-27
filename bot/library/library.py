
import telebot
import requests
import json
import logging
import os
import sqlite3
import time


# Obtém o caminho absoluto para o arquivo configBot.json
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "..", "configBot.json")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

with open(config_path) as json_data_file:
    data = json.load(json_data_file)

DB_FILE = 'grupos.db'

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Criar uma tabela (se ainda não existir)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS grupos_telegram (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        nome TEXT
    )
''')

conn.close()
    
API_TOKEN = data['telegram']['token'] 
ID_ADMIN = data['telegram']['AdminId']
ID_BOOT = data['telegram']['Bot_ID']
ACOES = data['acoes']
BOT_TELEGRAM = telebot.TeleBot( API_TOKEN )
ACOES_OP = {} # list()
OP_SALVAS = {}
GANHO_ESPERADO= {} 

# def setBotConfig(botOri):
#     BOT_TELEGRAM = botOri

def sendMessageAllGroup(msg):
    for grupo_id in getGrupos():
            BOT_TELEGRAM.send_message(grupo_id[1], msg)
            time.sleep(2)

def getDataConfig():
    return data;

def getGrupos():
    # return data['telegram']['grupos'];
    
    return todosGrupos()

def getAtivos():
    return data['acoes'];


def getOperacoes():
    return data['operacao'];

def getOperacao(op):
    return data['operacao'][op];

def remove_group_id(chat_id):
    if grupo_existe(chat_id):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM grupos_telegram WHERE chat_id = (?)', (chat_id,))
        conn.commit()
        conn.close()

def add_group_id(chat_id, nome):
    if not grupo_existe(chat_id):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO grupos_telegram (chat_id, nome) VALUES (?, ?)', (chat_id,nome))
        conn.commit()
        conn.close()
        BOT_TELEGRAM.send_message(chat_id, "agora estou no grupo 👊") 
        
    
    # if not (str(chat_id) in data['telegram']['grupos']):
    #     data['telegram']['grupos'].append(str(chat_id))
    #     with open("configBot.json", "w") as json_file:
    #         json.dump(data, json_file, indent=4)
    #        

def grupo_existe(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM grupos_telegram WHERE chat_id = ?', (chat_id,))
    resultado = cursor.fetchone()

    conn.close()

    return resultado is not None
   
def todosGrupos():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM grupos_telegram')
    resultados = cursor.fetchall()

    conn.close()

    # Retorna todos os grupos
    return resultados   
   
def printTime(start_time, end_time, msg=""):
    execution_time = end_time - start_time
    hours, remainder = divmod(execution_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"{msg} :: Tempo de execucao: {int(hours)} horas, {int(minutes)} minutos, {int(seconds)} segundos")
    
       
        
def buscaGrupo():
    url = f'https://api.telegram.org/bot{API_TOKEN}/getUpdates'

    response = requests.get(url)
    data = response.json()

    chats = getGrupos()
    # print(data)  
    for update in data['result']:
        if 'message' in update:
            chat_id = update['message']['chat']['id']
            if chat_id not in chats:
                chats.append(chat_id)
                add_group_id(chat_id)

    print(chats)        