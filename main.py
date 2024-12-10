import asyncio
import json
import os

from telebot.async_telebot import AsyncTeleBot

from model_former import PatModel

bot = AsyncTeleBot('7877867673:AAEnQ7zOUM1qmcTkpusvBin_jPtjrcOeK68')

if not os.path.exists("users"):
    os.mkdir("users")

model = PatModel(
"sk-proj-jV89dvc6yJsm4mPMw4Jet9u03tkMvMvPUpiC65lPiwXBgqzKq2WP7jHEwBlxiAGLZQWG3kbNH_T3BlbkFJxRXw5llEE7HKnTOcI6-x"
"-1zAHq9N97S4J6RHHKf5UInkknUYGPsyaN2QnbCylhHj9H58Qt13wA","http://ucFtqS:92aPdD@196.18.14.7:8000")
model.load_model("gpt-3.5-turbo-1106", 5)

info = """Доступные функции:
*   Сложение чисел.
*   Предоставление информации о патенте по его номеру.
Запросы могут долго обрабатываться. В связи с введёнными ограничениями, для подключения к OpenAI API используется германский прокси.
Текущая модель: {}
Максимальное кол-во сообщений, хранящихся в памяти модели: {}""".format(model.model, model.memory_cells)

@bot.message_handler(commands=['start', 'info'])
async def start(message):
    await bot.send_message(chat_id=message.chat.id,
                           text="Привет! Я ИИ-ассистент в сфере интеллектуальной собственности. Могу отвечать на вопрос"
                                "ы, связанные с данной сферой, и выполнять некоторые функции. "+info)

@bot.message_handler(commands=['clear'])
async def clear(message):
    model.clear_message_history(fr"users/{message.chat.id}.json")
    await bot.send_message(chat_id=message.chat.id, text='История очищена!')

@bot.message_handler(content_types=['text'])
async def msg(message):
    send_message = await bot.send_message(chat_id=message.chat.id, text='Обрабатываю запрос, пожалуйста подождите!')
    answer = await model.get_response(message.text, fr"users/{message.chat.id}.json")
    await bot.edit_message_text(text=answer, chat_id=message.chat.id, message_id=send_message.message_id)

asyncio.run(bot.infinity_polling())
