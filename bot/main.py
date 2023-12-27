import asyncio
import threading
import telebot
# import library as bib
import time
from datetime import datetime
# from MetaTrader5 import *

import json 

from telebot import types

# import sys
# sys.path.append('./library') 
# sys.path.append('./estrategias') 

from library import library
from estrategias import estrategias

# from library import API_TOKEN, ID_ADMIN, getGrupos, getDataConfig, remove_group_id, add_group_id, log
# from estrategias import box3Pontas, MT5Initialize, mt5

############################### BOT COMANDOS ###################################################


# Configurar o bot do Telegram
# bot_token = '6107532977:AAE3GMixQILS9o-E2610Mdfy7cOCctevCOM'
bot = library.BOT_TELEGRAM # telebot.TeleBot( library.API_TOKEN )
estrategias.MT5Initialize() 


# Inicialinado Bot
library.log.info("Carregando configuracoes do Robo")
start_time = time.time()
for ac in library.getAtivos():
    estrategias.removeOptions(ac)
    code = estrategias.getOptionsComDesvioPadrao(ac)    
end_time = time.time()
library.printTime(start_time, end_time, "Loading")
         
 
# json_string = library.ACOES_OP['USIM5']   # code.to_json(orient='records')

# print(json_string)

######################################## COMANDO DO BOT EM GRUPO ##########################################################

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'],commands=['help'])
def handle_group_message_oi(message):
    # library.log.info(message)
    # Verificar se a mensagem contém um comando válido
    bot.reply_to(message, f' oi {message.from_user.first_name}, aqui alguns comandos, \n tenha boas operações')
    time.sleep(1)
    bot.send_message(message.chat.id, f'/ativos')
    time.sleep(1)
    bot.send_message(message.chat.id, f'/estrategias')
    time.sleep(1)
    bot.send_message(message.chat.id, f'/operacoes')
    time.sleep(1)
    bot.send_message(message.chat.id, f'/preco PETR4')

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'],commands=['ativos'])
def handle_group_message_ativos(message):
    
    # library.log.info(message)
    for atv in library.getAtivos():
        bot.send_message(message.chat.id, f'{atv}')
        time.sleep(1)

@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'],commands=['estrategias'])
def handle_group_message_estrategias(message):
    
    # library.log.info(message)
    for op in library.getOperacoes():
        bot.send_message(message.chat.id, f'{op}')
        time.sleep(1)


@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'],commands=['operacoes'])
def handle_group_message_estrategias(message):
    
    # library.log.info(message)
    msg = estrategias.verificaOperacao()
    for m in msg:
        bot.send_message(message.chat.id, m)
        time.sleep(1)
    # for chave, opcao in library.OP_SALVAS.items():
    #     bot.send_message(message.chat.id, f'ID: {chave} : Ativo: {opcao["ativo"]}, operação: {opcao["operacao"]}, ganho: {opcao["ganho"]}')
    #     time.sleep(0.5)
        
        
# Lidar com a mensagem recebida em um grupo
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], commands=['preco'])
def handle_group_message_preco(message):
    try:
        if len(message.text.split()) >= 2:
            symbol = message.text.split()[1]
            library.log.info(symbol)
            
            # Obter o preço do último fechamento
            print(estrategias)
            preco = estrategias.getPrecoAtivo(symbol)
            
            if preco  > 0:
                bot.reply_to(message, f'O preço atual de {symbol} é: {preco}')
            else:
                bot.reply_to(message, f'Não foi possível obter o preço de {symbol}')
        else:
            bot.reply_to(message, 'Por favor, forneça um símbolo de ação/opção válido após o comando /preco.')
    
    except Exception as e:
        library.log.error(str(e))
        bot.reply_to(message, f'Ocorreu um erro: {str(e)}')
    
      
# # Chat id can be private or supergroups.
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup']  and str(message.from_user.id) == library.ID_ADMIN, commands=['admin']) 
def admin_rep(message):
    bot.send_message(message.chat.id, "You are allowed to use this command.")


@bot.message_handler(func=lambda message: message.chat.type == 'private' and str(message.from_user.id) == library.ID_ADMIN, commands=['grupos'])
def echo_all(message):
	# bot.reply_to(message, message.text)
    # library.log.info(message)
    grupos = library.getGrupos()
    library.log.info(grupos)
    if (len(grupos) == 0 ):
        bot.send_message(message.chat.id, f'Não há grupos')
 
    for atv in grupos:
        bot.send_message(message.chat.id, f'{atv[1]} - {atv[2]}')
        time.sleep(1)

# Ignorar todas as mensagens privadas, exceto do administrador definido
@bot.message_handler(func=lambda message: message.chat.type == 'private' and str(message.from_user.id) != library.ID_ADMIN)
def ignore_private_messages(message):
    pass

@bot.message_handler(func=lambda message: True, content_types=['new_chat_members', 'left_chat_member'])
def handle_new_chat_member(message):
    # library.log.info(message)
    if 'new_chat_member' in message.json:
        for new_member in message.new_chat_members:
            if library.ID_BOOT == str(new_member.id): 
                if str(message.from_user.id) == library.ID_ADMIN:                          
                    bot.send_message(message.chat.id, "Fui adicionado ao grupo 🤫, agora vamos procurar oportunidades em opções!")
                    bot.send_message(library.ID_ADMIN, "Fui adicionado ao grupo {chat_id} - {nome}".format(chat_id=message.chat.id,nome=message.chat.title))
                    library.add_group_id(message.chat.id, message.chat.title)
                else:
                    bot.send_message(message.chat.id, "Alguém me adicionou no grupo indevidamente. Até a próxima!")
                    bot.send_message(library.ID_ADMIN, "Fui adicionado indevidamente ao grupo {chat_id} - {nome}".format(chat_id=message.chat.id,nome=message.chat.title))
                    bot.leave_chat(message.chat.id)
                    
            else:   
                bot.send_message(message.chat.id, f"Olá {new_member.first_name}! Bem-vindo(a) ao grupo.") 
            
    elif 'left_chat_member' in message.json:
        if library.ID_BOOT == str(message.left_chat_member.id): 
            library.remove_group_id(message.chat.id)
            # if str(message.from_user.id) == library.ID_ADMIN:  
            # bot.send_message(message.chat.id, "Fui removido do grupo. 😢")


library.log.info("Estrategias Carregadas ...")

def update_prices_thread():
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(estrategias.update_prices())
        time.sleep(10)
        # print('novo ciclo')

update_thread = threading.Thread(target=update_prices_thread)
update_thread.start()


def Box3P_thread():
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(estrategias.search_box3Pontas())
        time.sleep(10)
        
box3P_thread = threading.Thread(target=Box3P_thread)
box3P_thread.start()


def SBTH_thread():
    while True:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(estrategias.search_SBTH())
        time.sleep(10)
        
SBTH_thread = threading.Thread(target=SBTH_thread)
SBTH_thread.start()



library.sendMessageAllGroup("Olá Pessoal, estou pronto, procurando oportunidades...💵")   

    
bot.polling()
