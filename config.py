WELCOME_MSG = ('Вы запустили бота по парсингу сайта ВкусВилл (далее ВВ).\n'
               'Порядок работы с ботом следующий:\n'
               '1). Пришлите ссылку на интересуемый вас товар с сайта ВВ;\n'
               '2). Я обработаю эту ссылу и, если смогу определить '
               'наименование товара и его стоимость, - предложу вам оплалить '
               'парсинг данного товара.\n'
               '3). После оплаты вам необходимо подтвердить ссылку для парсинга, '
               'для этого достаточно нажать на кнопку с текстом "Да" расположенную '
               'под сообщением с результатами её обработки.\n'
               '4). В стоимость работы входит ежедневный мониторинг цены и её '
               'сохранение в базу данных, из которой вам в конце месяца '
               'будут направляться данные в текстовом формате для обработки в '
               'аналитической программе наподобии Excel или Power BI. \n'
               'В результате, у вас будут необходимые данные для расчёта '
               'динамики цен, на сбор которых вы не потратите и 1 секунды.\n'
               '5). Стоимость парсинга одной ссылки составляет 1 рубль в день. '
               'Минимальная сумма платежа составляет 31 рубль и не подлежит '
               'возврату. Услуга считается оказанной с момента оплаты и акт '
               'оказания услуг считается подписанным обеими соторонами с момента '
               'получения сторонами подтверждения факта оплаты от Платёжной '
               'системы.\n')

WRONG_URL = 'Ссылка должна начинаться с https://vkusvill.ru'
WRONG_PARSING = ('Что-то не так с ссылкой, я не могу её корректно обработать, '
                 'прощу прощения.')
ER_PERMISSION = 'Ошибка: недостаточно прав для чтения файла.'

VV_CLASS_PRODUCT = 'Product__title js-datalayer-catalog-list-name'
VV_CLASS_PRICE = 'Price__value'
VV_CLASS_PRODUCT_Page = '_detailProdPage'

F_PAYS = 'Pays/'
F_TASKS = 'Tasks/'
F_PARSING = 'Parsing results/'

SUM_PAY = 100.00
FORMAT_DATETIME = '%Y.%m.%d--%H-%M-%S'