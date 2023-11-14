import telebot
from telebot import types

import warnings

warnings.filterwarnings('ignore')

import requests
from bs4 import BeautifulSoup
from datetime import date

import config
import token

bot = telebot.TeleBot(token.TOKEN)


def answer_user(msg, answer: str, button_yes_no: bool = False):
    if button_yes_no == False:
        bot.send_message(msg.chat.id, answer)
    elif button_yes_no == True:
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_yes, key_no)
        bot.send_message(msg.chat.id, answer, reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def hello_new_user(message):
    answer_user(message, config.WELCOME_MSG)


@bot.message_handler(content_types=['text'])
def url_message(message):
    if not message.text.startswith('https://vkusvill.ru'):
        answer_user(message, config.WRONG_URL)
    else:
        product, price, url_product = parsing(message)
        if product == False or price == False:
            answer_user(message, config.WRONG_PARSING)
        else:
            answer_user(message,
                        f'Товар "{product}", цена {price}. '
                        f'Ссылка {url_product}',
                        button_yes_no=True)


@bot.callback_query_handler(func=lambda call: True)
def get_offer(call):
    if call.data == 'yes':
        answer_user(call.message, 'Вы нажали Да ...')
        check_balance(call)
    elif call.data == 'no':
        answer_user(call.message, 'Если передумаете - нажмите Да.')


def check_balance(call):
    # проверка наличия файла с именем = id пользователя
    # - создание файла, если его нет
    # проверка баланса пользователя
    #  - строрнирование баланса если он положительный
    # ответ пользователю:
    #  - ссылка поставлена на мониторинг
    #  - требуется оплата в размере ... и отправка ссылки для оплаты
    answer_user(call.message, f'Проверяю баланс для ссылки '
                              f'{call.message.text.split()[-1]}')



def parsing(msg) -> list:
    bot.send_message(msg.chat.id, 'Запускаю парсинг ссылки ...')
    # current_date = date.today().strftime('%Y.%m.%d')

    response = requests.get(msg.text)
    soup = BeautifulSoup(response.text, 'lxml')

    chek = soup.findAll('body', class_='_detailProdPage')
    if len(chek):
        product = soup.find('h1', class_=config.VV_CLASS_PRODUCT)
        price = soup.find('span', class_=config.VV_CLASS_PRICE)
        return [product.text.strip(), price.text.strip(), msg.text]

    return [False, False]


if __name__ == '__main__':
    print('Бот запущен ...')
    # while True:
    #     try:
    bot.infinity_polling()
    print('не работает ...')
    # except:
    #     pass

# resize_keyboard - использовать в клавиатуре телеграмма для адапатации под разные устройства
# t.me/parsingYouAndMyBot
# def test(f, d: int = 1, *args, **kwargs):
