from datetime import datetime
from time import sleep
from warnings import filterwarnings

filterwarnings('ignore')

from telebot import TeleBot
from telebot import types
from requests import ReadTimeout

import config
import token_tg
import logic

bot = TeleBot(token_tg.TOKEN)


def answer_user(msg: types.Message, answer: str,
                button_yes_no: bool = False) -> None:
    """
    Возвращаем ответ пользователю в чат телеграм
    :param msg: сообщение в чате телеграма
    :param answer: тест ответа пользователю для отправки в чат телеграма
    :param button_yes_no: отображаем или нет кнопки Да/Нет под сообщением
    :return: функция ничего не возвращает
    """
    if button_yes_no == False:
        bot.send_message(msg.chat.id, answer)
    elif button_yes_no == True:
        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_yes, key_no)
        bot.send_message(msg.chat.id, answer, reply_markup=keyboard)


@bot.message_handler(commands=['start'])
def hello_new_user(message: types.Message) -> None:
    """
    Приветствуем нового пользователя
    :param message: сообщение в чате телеграма
    :return: функция ничего не возвращает
    """
    answer_user(message, config.WELCOME_MSG)


@bot.message_handler(content_types=['text'])
def url_message(message: types.Message) -> None:
    """
    Функция анализирует сообщение пользователя на корректность ссылки
    :param message: сообщение в чате телеграма
    :return: функция ничего не возвращает
    """
    if not message.text.startswith('https://vkusvill.ru'):
        answer_user(message, config.WRONG_URL)
    else:
        bot.send_message(message.chat.id, 'Запускаю парсинг ссылки ...')
        product, price = logic.parsing(message.text)
        url_product = message.text.strip()
        if (product or price or url_product) is False:
            answer_user(message, config.WRONG_PARSING)
        else:
            answer_user(message,
                        f'Товар "{product}", цена {price}. '
                        f'Ссылка {url_product}',
                        button_yes_no=True)


@bot.callback_query_handler(func=lambda call: True)
def get_offer(call: types.CallbackQuery) -> None:
    """
    Функция обрабатывает ответ пользователя через кнопки под сообщением
    :param call: нажатые кнопки вместе с сообщением из чата телеграм
    :return: функция ничего не возвращает
    """
    if call.data == 'yes':
        answer_user(call.message, 'Вы нажали Да ...')
        logic.check_balance(call)
    elif call.data == 'no':
        answer_user(call.message, 'Если передумаете - нажмите Да.')


def turn_on_bot() -> None:
    try:
        print('Включил телеграм бота.')
        bot.infinity_polling()
    except (ConnectionError, ReadTimeout) as e:
        current_date = datetime.now().strftime(config.FORMAT_DATETIME)
        print(f'Произошёл сбой в работе Телеграм бота!\n'
              f'- время сбоая {current_date};\n'
              f'- ошибка {e};\n'
              f'Перезапущу бота через 5 сек.')
        sleep(5)


if __name__ == '__main__':
    while True:
        logic.turn_on_time_broker()
        turn_on_bot()
        print('Телеграм бот отключен!')
