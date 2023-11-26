from datetime import datetime
from threading import Thread
from typing import Union
from time import sleep
from os import listdir

from requests import ConnectTimeout
from requests import ReadTimeout
from requests import request
from telebot import types
from bs4 import BeautifulSoup

import main
import config


def check_balance(call: types.CallbackQuery) -> bool:
    """
    Функция проверяет баланс пользователя. Если баланаса недостаточно -
    то запускает функционал для его пополнения. В противном случае
    запускается функционал добавления ссылки в файл для мониторинга.
    :param call: нажатые кнопки вместе с сообщением из чата телеграм
    :return: если баланса достаточно - возвращает True, иначе False
    """
    main.answer_user(call.message, f'Проверяю баланс для ссылки '
                                   f'{call.message.text.split()[-1]}')

    check_exist_user(call.message.chat.id)
    check_sum = check_sum_user(call.message.chat.id, config.SUM_PAY)
    if not check_sum:
        main.answer_user(call.message, 'Необходима оплата.')
        pay_work(call.message, config.SUM_PAY)
        print('Оплата ссылки выполнена')
        check_sum = check_sum_user(call.message.chat.id, config.SUM_PAY)

    if check_sum:
        add_task(call.message.chat.id, call.message.text.split()[-1])
        print('Ссылка добавлена в файл для парсинга')
        main.answer_user(call.message, 'Мониторинг товара запущен!')

    return check_sum


def add_task(user_id: int, url: str) -> bool:
    """
    Функция добавления ссылки в список для мониторинга цены товара
    :param user_id: идентификатор пользователя в телеграм (уникальный)
    :param url: ссылка на ВВ для мониторинга
    :return: True - если функция отработала корректно, иначе False
    """
    path = config.F_TASKS + str(user_id)
    try:
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


def pay_work(msg, sum_pay: int) -> bool:
    """
    Функция имитирующая оплату пользователем работы чат-бота телеграм.
    :param msg: сообщение из чата в телеграм для ответа пользователю
    :param sum_pay: сумма для оплаты работы чат-бота телеграм
    :return: True - функция отработала корректно
    """
    main.answer_user(msg, 'Перейдите по ссылке ниже для оплаты ...')
    main.answer_user(msg, 'Оплата успешно выполнена!')
    write_pay(msg.chat.id, sum_pay)
    return True


def write_pay(user_id, sum_pay: int) -> bool:
    """
    Функция записывает оплаченную сумму пользователем в файл с его балансом.
    :param user_id: идентификатор пользователя в телеграм (уникальный)
    :param sum_pay: сумма для оплаты работы чат-бота телеграм
    :return: True - если функция отработала корректно, иначе False
    """
    try:
        path = config.F_PAYS + str(user_id)
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        with open(path, 'r+', encoding='utf-8') as file:
            balance = file.readlines()[-1]
            balance = float(balance.split()[-1]) + sum_pay
            file.seek(0)
            if file.read() == '':
                file.write(f'{current_date} {balance}')
            else:
                file.write(f'\n{current_date} {balance}')
        return True
    except PermissionError:
        print('Ошибка: недостаточно прав для работы с файлом.')

    return False


def check_sum_user(user_id: int, sum_pay: int) -> bool:
    """
    Функция проверяем наличие необходимой суммы на балансе пользователя.
    Если баланса достаточно - списывает его. Иначе ничего не списывает.
    :param user_id: идентификатор пользователя в телеграм (уникальный)
    :param sum_pay: сумма для оплаты работы чат-бота телеграм
    :return: True - если функция отработала корректно, иначе False
    """
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


def check_exist_user(user_id: int) -> bool:
    """
    Функция проверяет существование пользователя в базе. Если пользователь
    новый - создаёт для него необходимый файл (имя файла = user_id).
    :param user_id: идентификатор пользователя в телеграм (уникальный)
    :return: True - если функция отработала корректно, иначе False
    """
    path = config.F_PAYS + str(user_id)
    try:
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


def parsing(url: str, ) -> tuple:
    """
    Функция для получения данных по товару с сайта ВВ.
    :param url: адрес карточки товара на сайте ВВ.
    :return: True - если функция отработала корректно, иначе False
    """
    try:
        response = request('GET', url=url, verify=False, timeout=15)
    except (ConnectTimeout, ReadTimeout) as e:
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        print(f'Произошёл сбой в парсинге сайта!\n'
              f'- время сбоая {current_date};\n'
              f'- ошибка {e};\n'
              f'Перезапущу парсинг через 5 сек.')
        sleep(5)
        return (False,)

    soup = BeautifulSoup(response.text, 'lxml')
    check = soup.findAll('body', class_=config.VV_CLASS_PRODUCT_Page)
    if len(check):
        product = soup.find('h1', class_=config.VV_CLASS_PRODUCT)
        price = soup.find('span', class_=config.VV_CLASS_PRICE)
        return (product.text.strip(), price.text.strip())

    return (False,)


def database_update() -> bool:
    """
    Функция для обновления базы данных по товарам.
    :return: True - если функция отработала корректно, иначе False
    """
    for file in listdir(config.F_TASKS):
        print(f'Обрабатываю файл {file}')
        all_url = read_file(f'{config.F_TASKS}{file}')
        brutto_url = ''

        for url in all_url:
            print(f'- обрабатываю ссылку {url.strip()}')
            sleep(15)
            product, price = parsing(url.strip())
            current_date = datetime.now().strftime(config.FORMAT_DATETIME)
            if product and price:
                brutto_url += f'{current_date} {product} {price}\n'
            else:
                print(f'- из файла {file} бот не может распарсить {url} ')

        write_file(f'{config.F_PARSING}{file}', brutto_url)

    return True


def write_file(name_file: str, add_text: str, mode: str = 'a') -> bool:
    """
    Функция записывает результаты парсинга сайта в файл пользователя
    :param name_file: имя файла для хранения результатов работы парсера
    :param add_text: результаты работы парсера
    :param mode: режим открытия файла
    :return: True - если функция отработала корректно, иначе False
    """
    try:
        with open(name_file, mode, encoding='utf-8') as file:
            file.write(add_text)
            print(f'Результаты парсинга записаны в файл {name_file}\n')
    except FileNotFoundError:
        print('Ошибка: файл не найден! Приступаю к его созданию ...')
        write_file(name_file, add_text, mode='w')
    except PermissionError:
        print(config.ER_PERMISSION)
        return False

    return True


def read_file(user_file: str, mode: str = 'r') -> Union[list[str], bool]:
    """
    Функция для получения всех ссылок на карточки товаров для обработки
    :param user_file: имя файла с ссылками для обработки
    :param mode: режим открытия файла
    :return: список с ссылками - если функция отработала корректно,
             иначе False
    """
    try:
        with open(user_file, mode, encoding='utf-8') as file:
            return file.readlines()
    except PermissionError:
        print(config.ER_PERMISSION)
        return False


def time_broker() -> None:
    """
    Функция для запуска обновления цен с необходимой регулярностью
    :return: функция ничего не возвращает
    """
    while True:
        sleep(3)  # ожидаем запуска телеграм бота
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        print(f'Приступил к обновлению цен в {current_date}')
        database_update()
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        print(f'Обновление цен завершено в {current_date}')
        sleep(3600)  # каждый час обновляем данные


def turn_on_time_broker() -> None:
    try:
        print('Включил тайм-брокер.')
        thread = Thread(target=time_broker)
        thread.start()
    except Exception as e:
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        print(f'Произошёл сбой в работе тайм-брокера!\n'
              f'- время сбоая {current_date};\n'
              f'- ошибка {e};\n'
              f'Перезапущу тайм-брокера через 5 сек.')
        sleep(5)
