import os
import logging
from matplotlib.pyplot import imread, imsave
import numpy as np
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters


updater = Updater(token=os.environ.get('TOKEN'), use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


questions = [
    '',
    'How do you feel right now?',
    'Have you helped anyone today? How?',
    'What are you grateful for?'
]


user_data = {}


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please send me a selfie to start!")

start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


def selfie(update, context):
    file = context.bot.getFile(update.message.photo[-1].file_id)
    file.download('image.png')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Please upload your selfie to start")


def selfie(update, context):
    username = update.effective_chat.username
    if update.message.photo:
        file = context.bot.getFile(update.message.photo[-1].file_id)
        file.download(f'{username}.jpg')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Selfie saved, thanks!')
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Would you like to start mental state questionnaire now?')


selfie_handler = MessageHandler(Filters.photo, selfie)
dispatcher.add_handler(selfie_handler)


def update_photo(filename):
    image = imread(filename)
    lum_img = image[:,:,::-1]
    imsave(filename, lum_img)


def questionnaire(update, context):
    username = update.effective_chat.username
    if username not in user_data:
        user_data[username] = {'answers': {}}
    current_answer_num = len(user_data[username]['answers'].keys()) - 1
    logging.info(f'current_answer_num {current_answer_num}')
    user_data[username]['answers'][questions[current_answer_num - 1]] = update.message.text
    if current_answer_num + 2 >= len(questions):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='You have answered all the questions for today. Here is how your portrait look like')
        update_photo(f'{username}.jpg')
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(f'{username}.jpg', 'rb'))
        return
    answers = user_data[username]['answers']
    if len(answers) < len(questions):
        context.bot.send_message(chat_id=update.effective_chat.id, text=questions[len(answers)])
    logging.info(f'{username} {user_data}')


echo_handler = MessageHandler(Filters.text, questionnaire)
dispatcher.add_handler(echo_handler)


updater.start_polling()