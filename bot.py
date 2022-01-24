import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton
from aiogram.types import reply_keyboard

from copy import deepcopy
import os
from urllib.parse import urljoin

from config import *

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

class User_INFO:
    def __init__(self):
        self.photos = []
        self.wait_photos = None

buffer = {}

start_kb = InlineKeyboardMarkup()
start_kb.add( InlineKeyboardButton('Transfer style from one picture to another', callback_data='style') )

settings_kb = InlineKeyboardMarkup()
settings_kb.add( InlineKeyboardButton('Default', callback_data='default') )
settings_kb.add( InlineKeyboardButton('Back', callback_data='menu') )

back_kb = InlineKeyboardMarkup()
back_kb.add( InlineKeyboardButton('Back', callback_data='menu'))

#/start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, f"Hi {message.from_user.first_name}! I'm Style transfer bot.\n"
    + "I can transfer style from one picture to another.\n" + "What I can:", reply_markup=start_kb)

    buffer[message.chat.id] = User_INFO()


#/help
@dp.message_handler(commands=['help'])
async def send_help(message: types.Message):
    await bot.send_message(message.chat.id, "What I can:", reply_markup=start_kb)

#Back to menu
@dp.callback_query_handler(lambda c: c.data == 'menu')
async def menu(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("What I can:")
    await callback_query.message.edit_reply_markup(reply_markup=start_kb)

# style transfer
@dp.callback_query_handler(lambda c: c.data == 'style')
async def style(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Choose settings for transfer style:")
    await callback_query.message.edit_reply_markup(reply_markup = settings_kb)
    if callback_query.from_user.id not in buffer:
        buffer[callback_query.from_user.id] = User_INFO()

#default settings
@dp.callback_query_handler(lambda c: c.data == 'default')
async def default_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("1-st picture -- STYLE\n" 
    + "Send me a picture, the style from which you need to transfer.\n")
    await callback_query.message.edit_reply_markup(reply_markup=back_kb)
    buffer[callback_query.from_user.id].wait_photos = 2
    
# getting image
@dp.message_handler(content_types=['photo', 'document'])
async def get_image(message):
    if message.content_type == 'photo':
        img = message.photo[-1]

    else:
        img = message.document
        if img.mime_type[:5] != 'image':
            await bot.send_message(message.chat.id,
                "Upload a file in image format.",
                reply_markup=start_kb)
            return

    file_info = await bot.get_file(img.file_id)
    photo = await bot.download_file(file_info.file_path)

    buffer[message.chat.id].photos.append(photo)

    if buffer[message.chat.id].wait_photos == 2:
        buffer[message.chat.id].wait_photos = 1
        await bot.send_message(message.chat.id,"2-d picture -- PICTURE\n" 
        + "Send me a picture to which you need to transfer this style.",reply_markup=back_kb)

    elif buffer[message.chat.id].wait_photos == 1:
        await bot.send_message(message.chat.id, "In process")

        # for debug
        try:
            #output = await style_transfer(Style_Transfer_CLASS, buffer[message.chat.id], *buffer[message.chat.id].photos)
            #await bot.send_document(message.chat.id, deepcopy(output))
            await bot.send_photo(message.chat.id, buffer[message.chat.id].photos[1])

        except RuntimeError as err:
            if str(err)[:19] == 'CUDA out of memory.':
                await bot.send_message(message.chat.id, "An error has occurred. I don't have enough memory to perform this action.")
            else:
                await bot.send_message(message.chat.id, "An error has occurred.")
        except Exception as err:
            await bot.send_message(message.chat.id, "An error has occurred.")

        await bot.send_message(message.chat.id, "So what do we do next?", reply_markup=start_kb)
    
        del buffer[message.chat.id]


async def on_startup(dp):
    await bot.set_webhook(webhook_url)
    # insert code here to run it after start

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    logging.warning('Bye!')
    # insert code here to run it before shutdown
    


if __name__ == '__main__':
    if CONNECTION_TYPE == 'POOLING':
        executor.start_polling(dp, skip_updates=True)

    elif CONNECTION_TYPE == 'WEBHOOK':
        webhook_path = f'/webhook/{API_TOKEN}'
        webhook_url  = f'{WEBHOOK_HOST}{webhook_path}'

        webapp_host = '0.0.0.0'
        webapp_port = int(os.environ.get('PORT', WEBAPP_PORT))

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=webhook_path,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=webapp_host,
            port=webapp_port,
        )