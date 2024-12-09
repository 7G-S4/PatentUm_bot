import json
import os

import telebot
from huggingface_hub import InferenceClient
from transformers import AutoModel

from model_former import PatModel

users_messages = 3



model = PatModel('DiTy/gemma-2-9b-it-russian-strict-function-calling-DPO')
model.load_model()

bot = telebot.TeleBot('7877867673:AAEnQ7zOUM1qmcTkpusvBin_jPtjrcOeK68')

if not os.path.exists("users"):
    os.mkdir("users")

@bot.message_handler(commands=['start', 'info'])
def start(message):
    bot.send_message(chat_id=message.chat.id,
                     text="""
Привет! Я ИИ-ассистент в сфере интеллектуальной собственности. Задавайте мне вопросы, касающейся данной темы, а я \
постараюсь вам помочь.
    """)

@bot.message_handler(commands=['clear'])
def clear(message):
    with open(f'users/{message.chat.id}.json', 'w', encoding='utf-8') as file:
        oldmes = {'text': [{"role": "system",
                                      "content": prompt}]}
        json.dump(oldmes, file, ensure_ascii=False)
    bot.send_message(chat_id=message.chat.id, text='История очищена!')

@bot.message_handler(commands=['reload'])
def reload(message):
    bot.send_message(chat_id=message.chat.id, text='Промпты модели обновлены!')

@bot.message_handler(content_types=['text'])
def msg(message):
    if f"{message.chat.id}.json" not in os.listdir('users'):
        with open(f"users/{message.chat.id}.json", "w", encoding='utf-8') as file:
            oldmes = {'text': [{"role": "system", "content": prompt}]}
            json.dump(oldmes, file, ensure_ascii=False)

    with open(f'users/{message.chat.id}.json', 'r', encoding='utf-8') as file:
        oldmes = json.load(file)

    try:
        send_message = bot.send_message(chat_id=message.chat.id, text='Обрабатываю запрос, пожалуйста подождите!')

        oldmes['text'].append({'role': 'user', 'content': message.text})
        #{'role': 'system', 'content': remind},
        ai_messages = (oldmes['text'][:-1] + [oldmes['generated_text'][-1]])
        res = client.chat_completion(
            messages=ai_messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=10000,
        )
        bot.edit_message_text(text=res.choices[0].message.tool_calls[0].function.name, chat_id=message.chat.id,
                              message_id=send_message.message_id)
        #oldmes['generated_text'].append(res[0]['generated_text'][-1])
        #with open(f'users/{message.chat.id}.json', 'w', encoding='utf-8') as file:
        #    k = 0
        #    n = len(oldmes['generated_text'])-1
        #    for ai_dict_idx in range(n, -1, -1):
        #        if oldmes['generated_text'][ai_dict_idx]['role'] == "user": k += 1
        #        if k > users_messages:
        #            del oldmes['generated_text'][ai_dict_idx+1]
        #            del oldmes['generated_text'][ai_dict_idx]
        #            break
        #    json.dump(oldmes, file, ensure_ascii=False)

    except Exception as e:
        bot.send_message(chat_id=message.chat.id, text="Ошибка:\n" + str(e))

bot.infinity_polling()
