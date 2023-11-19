import telebot

from telebot import types

import warnings

warnings.filterwarnings('ignore')

import requests
from requests import ConnectTimeout

from bs4 import BeautifulSoup
from datetime import datetime

import time
import threading
import os

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
        bot.send_message(message.chat.id, 'Запускаю парсинг ссылки ...')
        product, price, url_product = parsing(message.text)
        if product == False or price == False or url_product == False:
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
        print(config.ER_PERMISSION)
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
        print(config.ER_PERMISSION)
        return False


def parsing(url: str, back_url: bool = True) -> list:
    try:
        response = requests.request('GET', url=url, verify=False, timeout=10)
    except ConnectTimeout:
        if back_url:
            return [False, False, False]
        else:
            return [False, False]

    soup = BeautifulSoup(response.text, 'lxml')
    chek = soup.findAll('body', class_='_detailProdPage')
    if len(chek):
        product = soup.find('h1', class_=config.VV_CLASS_PRODUCT)
        price = soup.find('span', class_=config.VV_CLASS_PRICE)
        if back_url:
            return [product.text.strip(), price.text.strip(), url]
        else:
            return [product.text.strip(), price.text.strip()]

    if back_url:
        return [False, False, False]
    else:
        return [False, False]


def database_update() -> bool:
    for file in os.listdir(config.F_TASKS):
        print(f'Обрабатываю файл {file}')
        all_url = read_file(f'{config.F_TASKS}{file}')
        brutto_url = ''
        for url in all_url:
            print(f'- парсю ссылку {url.strip()} из спика ссылок {all_url}')
            product, price = parsing(url.strip(), False)
            time.sleep(3)
            current_date = datetime.now().strftime(config.FORMAT_DATETIME)
            if product and price:
                brutto_url += f'{current_date} {product} {price}\n'
            else:
                print(f'- из файла {file} бот не может распарсить {url} ')
        write_file(f'{config.F_PARSING}{file}', brutto_url)

    return True


def write_file(name_file: str, add_text: str, mode: str = 'a') -> bool:
    try:
        with open(name_file, mode, encoding='utf-8') as file:
            file.write(add_text)
            print(f'Результаты парсинга записаны в файл {name_file}')
    except FileNotFoundError:
        print('Ошибка: файл не найден! Приступаю к его созданию ...')
        write_file(name_file, add_text, mode='w')
    except PermissionError:
        print(config.ER_PERMISSION)
        return False

    return True


def read_file(user_file: str, mode: str = 'r'):
    try:
        with open(user_file, mode, encoding='utf-8') as file:
            return file.readlines()
    except PermissionError:
        print(config.ER_PERMISSION)
        return False


def time_broker():
    while True:
        print('Обновляю цены ...')
        database_update()
        print('Обновление завершено!')
        time.sleep(15)


if __name__ == '__main__':
    print('Телеграм-бот включён!')
    # while True:
    #     try:
    thread = threading.Thread(target=time_broker)
    thread.start()
    bot.infinity_polling()
    print('Телеграм-бот отключен!')
    # except:
    #     pass
