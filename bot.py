import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup
from aiogram.types import InlineKeyboardButton

import os
import numpy as np
from io import BytesIO

from config import *
from transfer_style_class import *

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

class User_INFO:
    def __init__(self):
        self.photos = []
        self.wait_photos = None
        self.imsize = 256
        self.num_steps = 500
        self.style_weight = 100000
        self.content_weight = 0.1
        self.params = None
        self.default = 0
    def change_imsize(self, i):
        self.imsize = i
    def change_num_steps(self, n):
        self.num_steps = n
    def change_style_weight(self, w):
        self.style_weight = w
    def change_content_weight(self, c):
        self.content_weight = c

users = {}

start_kb = InlineKeyboardMarkup()
start_kb.add(InlineKeyboardButton('Transfer style from one picture to another', callback_data='style'))

settings_kb = InlineKeyboardMarkup()
settings_kb.add(InlineKeyboardButton('Default', callback_data='default'))
settings_kb.add(InlineKeyboardButton('Personal', callback_data='personal'))
settings_kb.add(InlineKeyboardButton('Reset settings', callback_data='reset'))
settings_kb.add(InlineKeyboardButton('Back', callback_data='menu'))

back_kb = InlineKeyboardMarkup()
back_kb.add(InlineKeyboardButton('Back', callback_data='menu'))

settings_personal_kb = InlineKeyboardMarkup()
settings_personal_kb.add(InlineKeyboardButton('Image size', callback_data='imsize'))
settings_personal_kb.add(InlineKeyboardButton('Number of steps', callback_data='num_steps'))
settings_personal_kb.add(InlineKeyboardButton('Style weight', callback_data='style_weight'))
settings_personal_kb.add(InlineKeyboardButton('Content weight', callback_data='content_weight'))
settings_personal_kb.add(InlineKeyboardButton('Info', callback_data='info'))
settings_personal_kb.add(InlineKeyboardButton('Next', callback_data='next'))
settings_personal_kb.add(InlineKeyboardButton('Back', callback_data='menu'))

#/start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await bot.send_message(message.chat.id, f"Hi {message.from_user.first_name}! I'm Style-Transfer bot.\n"
    + "I can transfer style from one picture to another.\n" + "What I can:", reply_markup=start_kb)
    users[message.chat.id] = User_INFO()

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
    await callback_query.message.edit_text("Choose settings for transfer style:\n")
    await callback_query.message.edit_reply_markup(reply_markup = settings_kb)
    if callback_query.from_user.id not in users:
        users[callback_query.from_user.id] = User_INFO()

#default settings
@dp.callback_query_handler(lambda c: c.data == 'default')
async def default_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("1-st picture -- STYLE\n" 
    + "Send me a picture or document with a picture, the style from which you need to transfer.\n"
    + "IMPORTANT: Use the same image file formats for both pictures.\n")
    await callback_query.message.edit_reply_markup(reply_markup=back_kb)
    users[callback_query.from_user.id].wait_photos = 2
    users[callback_query.from_user.id].default = 0

@dp.callback_query_handler(lambda c: c.data == 'next')
async def personal_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("1-st picture -- STYLE\n" 
    + "Send me a picture or document with a picture, the style from which you need to transfer.\n"
    + "IMPORTANT: Use the same image file formats for both pictures.\n")
    await callback_query.message.edit_reply_markup(reply_markup=back_kb)
    users[callback_query.from_user.id].wait_photos = 2
    users[callback_query.from_user.id].default = 1

@dp.callback_query_handler(lambda c: c.data == 'personal')
async def personal_settings(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Choose the settings that you want to change.\n"
    + "If you don't want to change then click Next to continue.\n")
    await callback_query.message.edit_reply_markup(reply_markup=settings_personal_kb)

@dp.callback_query_handler(lambda c: c.data == 'imsize')
async def image_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Write the integer size of the image you would like to receive\n"
    + "For example: 128, 256, 512, 1024, ...", reply_markup=back_kb)
    users[callback_query.from_user.id].params = 1

@dp.callback_query_handler(lambda c: c.data == 'num_steps')
async def image_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Write the integer number of steps of the image you would like to receive\n"
    + "For example: 250, 300, 500, ...", reply_markup=back_kb)
    users[callback_query.from_user.id].params = 2

@dp.callback_query_handler(lambda c: c.data == 'style_weight')
async def image_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Write the style weight of the image you would like to receive\n"
    + "Recommend to use big positive numbers. (100000 >= ...)\n", reply_markup=back_kb)
    users[callback_query.from_user.id].params = 3

@dp.callback_query_handler(lambda c: c.data == 'content_weight')
async def image_set(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("Write the content weight of the image you would like to receive\n"
    +"Recommend to use small positive numbers. (... <= 1)", reply_markup=back_kb)
    users[callback_query.from_user.id].params = 4

@dp.message_handler(lambda message: message.text.isdigit())
async def params(message: types.Message):
    if users[message.chat.id].params == 1 and int(message.text) > 0:
        users[message.chat.id].change_imsize(int(message.text))
    elif users[message.chat.id].params == 2 and int(message.text) > 0:
        users[message.chat.id].change_num_steps(int(message.text))
    elif users[message.chat.id].params == 3 and float(message.text) > 0:
        users[message.chat.id].change_style_weight(float(message.text))
    elif users[message.chat.id].params == 4 and float(message.text) > 0:
        users[message.chat.id].change_content_weight(float(message.text))
    await bot.send_message(message.chat.id, "Would you like to change something else?\n"
    + "Otherwise, click Next.\n", reply_markup=settings_personal_kb)

@dp.message_handler(lambda message: not message.text.isdigit())
async def is_valid(message: types.Message):
    return await message.reply("Gotta be a number!\n (digits only)")

@dp.callback_query_handler(lambda c: c.data == 'reset')
async def menu(callback_query):
    await bot.answer_callback_query(callback_query.id)
    users[callback_query.from_user.id].imsize = 256
    users[callback_query.from_user.id].num_steps = 500
    users[callback_query.from_user.id].style_weight = 100000
    users[callback_query.from_user.id].content_weight = 0.1
    await callback_query.message.edit_text("Your personal settings have been reset.\n"
    + "INFO: Image size = {}, Number of steps = {}, Style weight = {}, Content weight = {}".format(users[callback_query.from_user.id].imsize,
    users[callback_query.from_user.id].num_steps, users[callback_query.from_user.id].style_weight, users[callback_query.from_user.id].content_weight), reply_markup=settings_kb)

@dp.callback_query_handler(lambda c: c.data == 'info')
async def menu(callback_query):
    await bot.answer_callback_query(callback_query.id)
    await callback_query.message.edit_text("INFO: Image size = {}, Number of steps = {}, Style weight = {}, Content weight = {}".format(users[callback_query.from_user.id].imsize,
    users[callback_query.from_user.id].num_steps, users[callback_query.from_user.id].style_weight, users[callback_query.from_user.id].content_weight), reply_markup=settings_personal_kb)

# getting image
@dp.message_handler(content_types=['photo', 'document'])
async def get_image(message):
    if message.content_type == 'photo':
        img = message.photo[-1]
    else:
        img = message.document
        if not set(":;!_*-+()#%&").isdisjoint(img.mime_type) or img.mime_type[:6] != 'image/':
            await bot.send_message(message.chat.id, "Upload a file in image format.", reply_markup=start_kb)
            return
    
    file = await bot.get_file(img.file_id)
    file_path = file.file_path
    photo = await bot.download_file(file_path)

    users[message.chat.id].photos.append(photo)

    if users[message.chat.id].wait_photos == 2:
        users[message.chat.id].wait_photos = 1
        await bot.send_message(message.chat.id,"2-d picture -- CONTENT\n" 
        + "Send me a picture or document with picture to which you need to transfer this style.\n"
        + "IMPORTANT: Use the same image file formats for both pictures.\n", reply_markup=back_kb)

    elif users[message.chat.id].wait_photos == 1:
        await bot.send_message(message.chat.id, "In process")
        try:
            input_img = await style_transfer(Style_Transfer, users[message.chat.id], users[message.chat.id].photos[0], users[message.chat.id].photos[1])
            await bot.send_document(message.chat.id, ('image', deepcopy(input_img)))
            await bot.send_photo(message.chat.id, input_img)
        except Exception as err:
            await bot.send_message(message.chat.id, "!! An error has occurred !!\nSome errors:\n"
            + "1. Check that images have the same format.\n"
            + "2. There may not be enough resources to process the image with your personal settings.\n")

        await bot.send_message(message.chat.id, "So what do we do next?", reply_markup=start_kb)
        del users[message.chat.id]


async def style_transfer(ST_Class, user, style_img, content_img):
    if user.default == 0: 
        st_class = ST_Class(style_img, content_img)
    elif user.default == 1:
        st_class = ST_Class(style_img, content_img, user.imsize, user.num_steps, user.style_weight, user.content_weight)
    input_img = await st_class.run_style_transfer()
    input_img = np.rollaxis(input_img.cpu().detach().numpy()[0], 0, 3)
    input_img = Image.fromarray((input_img * 255).astype('uint8'))
    input_img = img_to_media_obj(input_img)
    return input_img  


def img_to_media_obj(img):
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr
  

async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    # insert code here to run it after start

async def on_shutdown(dp):
    logging.warning('Shutting down..')
    logging.warning('Bye!')
    # insert code here to run it before shutdown
    


if __name__ == '__main__':
    if CONNECTION_TYPE == 'POOLING':
        executor.start_polling(dp, skip_updates=True)

    elif CONNECTION_TYPE == 'WEBHOOK':
        WEBHOOK_PATH = ''
        WEBHOOK_URL  = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
        WEBAPP_HOST = '0.0.0.0'
        WEBAPP_PORT = int(os.environ.get('PORT', 5000))

        executor.start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBAPP_HOST,
            port=WEBAPP_PORT,
        )