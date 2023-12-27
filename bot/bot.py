
import logging
import time
import MetaTrader5 as mt5
import json 
from io import StringIO
import logging
import os


from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

# dir_path = os.path.dirname(os.path.realpath(__file__))
# print(dir_path)

with open("configBot.json") as json_data_file:
    data = json.load(json_data_file)

apiToken = data['telegram']['token'] # '6107532977:AAE3GMixQILS9o-E2610Mdfy7cOCctevCOM'
# chatID = data['telegram']['chatID'] # '515382482'
adminID = data['telegram']['AdminId'] # '515382482'
# print(data)
acoes = data['acoes']

    #   ,'VALE3', 'PRIO3', 'SUZB3', 'FLRY3', 'BPAC11', 'LREN3' 
    # acoes = ['CPLE6', 'USIM5', 'PETR4','BBDC4', 'MRFG3', 'JBSS3', 'ITUB4', 'BBAS3', 'DXCO3',
    #          'SANB11', 'BBSE3', 'RANI3', 'BRKM5', 'KLBN11' ,'VIIA3', 'MGLU3', 'ITSA4', 'TIMS3', 
    #          'B3SA3', 'ABEV3', 'TRPL4', 'TAEE11', 'CMIG4', 'VBBR3', 'IRBR3', 'PETZ3', 'CIEL3', 
    #          'NTCO3', 'BRFS3', 'HYPE3', 'HAPV3', 'BOVA11', 'BBDC3', 'AMER3', 'SOMA3', 'WEGE3',
    #          'COGN3', 'YDUQ3', 'CYRE3', 'EZTC3', 'MRVE3', 'GGBR4', 'CSAN3', 'GOAU4', 'CSNA3', 'CMIN3', 
    #          'POSI3', 'BEEF3', 'ECOR3', 'ALPA4', 'AZUL4', 'CCRO3', 'QUAL3', 'RAIZ4', 'SAPR11', 'LWSA3'  ]    

def connectMT5(): 
    if not mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password']):
        # Caso não esteja conectado, realizar a conexão automaticamente       
        if not mt5.initialize(login=data['mt5']['account'], server=data['mt5']['server'],password=data['mt5']['password']):
            logger.info("Não foi possível conectar ao MetaTrader 5.")
            quit()
    else:
        logger.info("MetaTrader 5 conectado.")        


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Olá {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)


# Função para obter a cotação de uma ação
async def get_stock_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Obter o código da ação enviado pelo usuário
    stock_code = ""
    if context.args:
        stock_code = context.args[0].upper()
    else:
        stock_code = context.chat_data.get('stock_code', '').upper()

    # Obter os dados do mercado para a ação
    # connectMT5()
    mt5.symbol_select(stock_code,True)
    time.sleep(0.1) 
    symbol_info = mt5.symbol_info_tick(stock_code)
    if symbol_info is None:
        await update.message.reply_text(f'Não foi possível encontrar dados para a ação {stock_code}.')
        
        # update.callback_query.message.edit_text(message)
        return

    # Obter o preço atual da ação
    price = symbol_info.bid

    # Enviar a cotação da ação para o usuário
    if update.message:
        await update.message.reply_text(f'O preço atual da ação {stock_code} é de R$ {price:.2f}.')
    else:
        query = update.callback_query
        query.answer()
        await query.edit_message_text(text=f'O preço atual da ação {stock_code} é de R$ {price:.2f}.')
    #    // await update.callback_query.message.edit_text(f'O preço atual da ação {stock_code} é de R$ {price:.2f}.')
    
    mt5.symbol_select(stock_code,False)

# Função para lidar com a query que será chamada ao pressionar o botão
async def button_callback(update, context):
    query = update.callback_query
    data = query.data.split()
    if data[0] == 'get_stock_price':
        stock_code = data[1]
        context.chat_data['stock_code'] = stock_code
        await get_stock_price(update, context)

# Função para obter as ações monitoradas
async def get_stock_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    mensagem = ''
    keyboard = []

    for ativo in acoes:
        message_button = InlineKeyboardButton(f"📊 {ativo}", callback_data=f"get_stock_price {ativo}")
        keyboard.append([message_button])

    reply_markup = InlineKeyboardMarkup(keyboard)

    # Usa o objeto reply_markup ao enviar uma mensagem
    await update.message.reply_text('Segue a lista de ativos monitorados:', reply_markup=reply_markup)

# def message_handler(update, context):
#     chat_id = update.effective_chat.id

#     if chat_id < 0:
#         # Mensagem foi enviada em um grupo
#         # Processar a mensagem
#     else:
#         # Mensagem foi enviada em um chat privado
#         # Ignorar a mensagem ou responder com uma mensagem de erro
#         context.bot.send_message(chat_id=chat_id, text="Desculpe, eu só posso ser usado em grupos.")

async def block_private_chats(update, context):
    if update.effective_chat.type == 'private':
        # Se a mensagem foi enviada em conversa privada, não fazer nada
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Desculpe, eu só posso ser usado em grupos.")
        return
    
    # Se a mensagem foi enviada em grupo ou canal, responder normalmente
    # update.message.reply_text('Você disse: ' + update.message.text)

def is_admin(update: Update):
    # admin_id = 123456789 # substitua pelo ID do usuário admin
    return update.message.from_user.id == adminID

# inicializando a comunicação com o MT5
async def initMT5(app) -> None:
    """inicializando o bot."""
    # mt5.shutdown()
    logger.info("Conectando ao MetaTrader 5...")
    connectMT5()
    
async def finalizeMT5(app) -> None:
    """inicializando o bot."""
    logger.info("finalizando o MetaTrader 5...")
    mt5.shutdown()

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token. 6107532977:AAE3GMixQILS9o-E2610Mdfy7cOCctevCOM
    application = Application.builder().token(apiToken).post_init(initMT5).post_stop(finalizeMT5).build() 


    # on non command i.e message - echo the message on Telegram 
    block_private_chats_handler = MessageHandler((filters.TEXT | filters.COMMAND) & filters.ChatType.PRIVATE 
                                                 & filters.USER != adminID 
                                                 , block_private_chats)
    
    application.add_handler(block_private_chats_handler)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
   

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('price', get_stock_price))
    application.add_handler(CommandHandler('listar', get_stock_monitoring))
    
    application.add_handler(CallbackQueryHandler(button_callback))   


    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()