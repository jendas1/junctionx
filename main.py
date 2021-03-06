import os
import logging
from datetime import datetime

from matplotlib.pyplot import imread, imsave
import numpy as np
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pickler import get_full_user_data, save_user_data, save_all, load_all
from json import load, dump

BAD_EMOTION_THRESHOLD = 4
TOKEN = "868031376:AAGdASZ8GANAa3L5nyHZEZiHX4Yais8_DCg"
os.environ['TOKEN'] = TOKEN
updater = Updater(token=os.environ.get('TOKEN'), use_context=True)
dispatcher = updater.dispatcher
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

questions = [
    '',
    'How do you feel right now?',
    'Have you helped anyone today? How?',
    'What are you grateful for?',
    "How is your mood today? (answer with emoji)"
]

is_in_mood = set()

with open("emojimap.json", "r") as fp:
    emojimap = load(fp)


def start(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please send me a selfie to start!")


def next_day(update, context):
    username = update.effective_chat.username
    user_data = load_all()
    if username not in user_data:
        user_data[username] = {'answers': {}}
    if 'archive' not in user_data[username]:
        user_data[username]['archive'] = {}
    user_data[username]['archive'][datetime.now()] = user_data[username]['answers']
    user_data[username]['answers'] = {}
    save_all(user_data)
    start(update, context)


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


def update_photo(filename):
    image = imread(filename)
    lum_img = image[:, :, ::-1]
    imsave(filename, lum_img)


def emotionizer(answer):
    score = emojimap.get(answer[0:2], None)
    if score is None:
        score = emojimap.get(answer[0:1], None)
    if score is None:
        return 0.
    else:
        return float(score.get('score', 0.))


def questionnaire(update, context):
    username = update.effective_chat.username
    user_data = load_all()
    if username not in user_data:
        user_data[username] = {'answers': {}}
    current_answer_num = len(user_data[username]['answers'].keys()) - 1
    logging.info(f'current_answer_num {current_answer_num}')
    user_data[username]['answers'][questions[current_answer_num - 1]] = update.message.text
    if username in is_in_mood:
        answer = update.message.text
        is_in_mood.remove(username)
        user_emotion = emotionizer(answer)
        logging.info(f'emotion score is {user_emotion}')
        emotions = user_data[username].get("emotions", [])
        emotions.append(user_emotion)
        user_data[username]["emotions"] = emotions
        if len(emotions) >= BAD_EMOTION_THRESHOLD:
            state_bad = is_everything_bad(emotions)
            if state_bad:
                context.bot.send_message(chat_id=update.effective_chat.id,
                                         text="Hey! You've been constantly in a bad mood for 4 days. Maybe you should talk to your relatives or seek some aid?")
    answers = user_data[username]['answers']
    save_all(user_data)

    if current_answer_num + 2 >= len(questions):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='You have answered all the questions for today. Here is how your portrait look like')
        update_photo(f'{username}.jpg')
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=open(f'{username}.jpg', 'rb'))
        return
    if len(answers) < len(questions):
        bot_question = questions[len(answers)]
        if bot_question.split()[3] == "mood":
            is_in_mood.add(username)
        context.bot.send_message(chat_id=update.effective_chat.id, text=bot_question)
    logging.info(f'{username} {user_data}')


def is_everything_bad(emotions):
    for emotion in emotions[-BAD_EMOTION_THRESHOLD:]:
        if emotion >= 0:
            return False
    return True


if __name__ == '__main__':
    start_handler = CommandHandler('start', start)
    next_day_handler = CommandHandler('next', next_day)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(next_day_handler)
    selfie_handler = MessageHandler(Filters.photo, selfie)
    dispatcher.add_handler(selfie_handler)
    echo_handler = MessageHandler(Filters.text, questionnaire)
    dispatcher.add_handler(echo_handler)

    updater.start_polling()
