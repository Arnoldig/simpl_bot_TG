import telebot
from telebot import types

import warnings

warnings.filterwarnings('ignore')

import requests
from bs4 import BeautifulSoup
from datetime import datetime

import config
import token_tg

bot = telebot.TeleBot(token_tg.TOKEN)


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
    answer_user(call.message, f'Проверяю баланс для ссылки '
                              f'{call.message.text.split()[-1]}')

    chek_exist_user(call.message.chat.id)
    check_sum = check_sum_user(call.message.chat.id, config.SUM_PAY)
    if not check_sum:
        answer_user(call.message, 'Необходима оплата.')
        pay_work(call.message, config.SUM_PAY)
        print('Оплата ссылки выполнена')
        check_sum = check_sum_user(call.message.chat.id, config.SUM_PAY)

    if check_sum:
        add_task(call.message.chat.id, call.message.text.split()[-1])
        print('Ссылка добавлена в файл для парсинга')
        answer_user(call.message, 'Мониторинг товара запущен!')
        return True

    return False


def add_task(user_id: int, url: str) -> bool:
    try:
        path = config.F_TASKS + str(user_id)
        with open(path, 'r+', encoding='utf-8') as file:
            file.seek(0)
            if file.read() == '':
                file.write(f'{url}')
            else:
                file.write(f'\n{url}')
        return True
    except FileNotFoundError:
        print('Это новый пользователь - создаём файл для него.')
        with open(path, 'w', encoding='utf-8') as file:
            file.write(f'{url}')
        return True
    except PermissionError:
        print('Ошибка: недостаточно прав для чтения файла.')
        return False


def pay_work(msg: int, sum_pay: int) -> bool:
    # заглушка - пока что нет интеграции с платёжным сервисом по ссылке
    # направляем сообщение с ссылкой или кнопкой для оплаты
    answer_user(msg, 'Перейдите по ссылке ниже для оплаты ...')
    answer_user(msg, 'Оплата успешно выполнена!')
    # записываем оплату в файл пользователя
    write_pay(msg.chat.id, sum_pay)
    return True


def write_pay(user_id, sum_pay: int) -> bool:
    try:
        path = config.F_PAYS + str(user_id)
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        with open(path, 'r+', encoding='utf-8') as file:
            balanc = file.readlines()[-1]
            balanc = float(balanc.split()[-1]) + sum_pay
            file.seek(0)
            if file.read() == '':
                file.write(f'{current_date} {balanc}')
            else:
                file.write(f'\n{current_date} {balanc}')
        return True
    except PermissionError:
        print('Ошибка: недостаточно прав для работы с файлом.')

    return False


def check_sum_user(user_id: int, sum_pay: int) -> bool:
    try:
        path = config.F_PAYS + str(user_id)
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        with open(path, 'r+', encoding='utf-8') as file:
            new_file = False
            balance = file.readlines()[-1]
            balance = float(balance.split()[-1])
            file.seek(0)
            new_file = True if file.read() == '' else 0
            if balance >= sum_pay and new_file:
                file.write(f'{current_date} {balance - sum_pay}')
                return True
            elif balance >= sum_pay and not new_file:
                file.write(f'\n{current_date} {balance - sum_pay}')
                return True
    except PermissionError:
        print('Ошибка: недостаточно прав для работы с файлом.')

    return False


def chek_exist_user(user_id: int) -> bool:
    try:
        path = config.F_PAYS + str(user_id)
        with open(path, 'r', encoding='utf-8') as file:
            print('Пользователь есть в базе данных!')
        return True
    except FileNotFoundError:
        print('Это новый пользователь - создаём файл для него.')
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(f'{current_date} 0.00')
        return True
    except PermissionError:
        print('Ошибка: недостаточно прав для чтения файла.')
        return False


def parsing(msg) -> list:
    bot.send_message(msg.chat.id, 'Запускаю парсинг ссылки ...')

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
