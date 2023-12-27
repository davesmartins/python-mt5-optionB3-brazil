
import logging
import MetaTrader5 as mt5
import json 
from io import StringIO
import logging

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

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

with open("configBot.json") as json_data_file:
    data = json.load(json_data_file)

apiToken = data['telegram']['token'] # '6107532977:AAE3GMixQILS9o-E2610Mdfy7cOCctevCOM'
# chatID = data['telegram']['chatID'] # '515382482'

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
        rf"Hi {user.mention_html()}!",
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
    stock_code = context.args[0]
    print("ok.")

    # Obter os dados do mercado para a ação
    connectMT5()
    mt5.symbol_select(stock_code,True)
    symbol_info = mt5.symbol_info_tick(stock_code)
    if symbol_info is None:
        await update.message.reply_text(f'Não foi possível encontrar dados para a ação {stock_code}.')
        return

    # Obter o preço atual da ação
    price = symbol_info.bid

    # Enviar a cotação da ação para o usuário
    await update.message.reply_text(f'O preço atual da ação {stock_code} é de R$ {price:.2f}.')
    
    mt5.symbol_select(stock_code,False)

# inicializando a comunicação com o MT5
async def initMT5(app) -> None:
    """inicializando o bot."""
    # mt5.shutdown()
    logger.info("Conectando ao MetaTrader 5...")
    connectMT5()
    # await update.message.reply_text(update.message.text)

def main() -> None:
    
    
    """Start the bot."""
    # Create the Application and pass it your bot's token. 6107532977:AAE3GMixQILS9o-E2610Mdfy7cOCctevCOM
    application = Application.builder().token("6107532977:AAE3GMixQILS9o-E2610Mdfy7cOCctevCOM").post_init(initMT5).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler('price', get_stock_price))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()