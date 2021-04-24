from .config import ENGLISH, RUSSIAN, DEFAULT_LANG


ru_home_buttons = {
    'home_button': '🏠',
    'calculator_button': 'Калькулятор',
    'send_table_button': '✔️',
}
en_home_buttons = {
    'home_button': '🏠',
    'calculator_button': 'Calculator',
    'send_table_button': '✔️',
}

messages = {
    'ru': {
        'stop_message': 'Был рад помочь',
        'environment_message': 'Выберите среду выращивания',
        'filters_message': 'Напишите название бренда или продолжите выбор',
        'target_message': 'Выберите категорию или отправьте название бренда/удобрения',
        'continue_products_selecting_message': 'Продолжайте выбор',
        'storage_volume_message': 'Введите литраж',
        'checkout_message': 'Выбранные удобрения',
        'wait_for_table_message': 'Ваша таблица почти готова..',
        'os_message': 'Выберите вашу операционную систему',
        'start_cycle_date_message': 'Введите дату начала цикла (формат: гггг-мм-дд)',
        'email_message': 'Введите ваш email',
        'ios_calendar_instructions_message': """На вашу почту пришло письмо с файлом,
откройте его и добавьте в  календарь, нажав соответствующую кнопку""",
        'calendar_instructions_message': """Инструкция по добавлению в приложение календарь:
Android: https://support.google.com/calendar/answer/37118?co=GENIE.Platform%3DDesktop&hl=ru
Mac: откройте отправленный файл
""",

        'no_user_products_message': 'Вы еще ничего не добавили',
        'no_searched_products_message': 'Товара/бренда по запросу не найдено',
        'no_product_link_message': 'Подробной информации не найдено',
        'incorrect_storage_volume_message': 'Введите кол-во литров',

        'vega_base_button': 'База вега',
        'bloom_base_button': 'База цветение',
        'targets_button': 'Добавки',
        'different_products_button': 'Для разных растений',

        'add_product_button': 'В таблицу +',
        'remove_product_button': 'Удалить -',
        'product_link_button': 'Подробнее',

        'edit_products_button': 'Править',

        'download_xls_button': 'Скачать xls',
        'download_calendar_button️': 'Добавить в календарь',
    },

    'en': {
        'stop_message': 'Was glad to help you',
        'environment_message': 'Select a growing environment',
        'filters_message': 'Enter a brand name or continue selecting',
        'target_message': 'Select a category or send brand/product name',
        'continue_products_selecting_message': 'Продолжайте выбор',
        'storage_volume_message': 'Enter the litrage',
        'checkout_message': 'Selected products',
        'wait_for_table_message': 'Your table is almost ready..',
        'os_message': 'Select your OS',
        'start_cycle_date_message': 'Enter start growing cycle date (format: yyyy-mm-dd)',
        'email_message': 'Enter your email',
        'ios_calendar_instructions_message': 'We sent the email to you, open it and add to the calendar',
        'calendar_instructions_message': """Instructions for adding the calendar to your app:
Android: https://support.google.com/calendar/answer/37118?co=GENIE.Platform%3DDesktop&hl=ru
Mac: just open the file
""",

        'no_user_products_message': 'You did not add any product',
        'no_searched_products_message': 'Товара/бренда по запросу не найдено',
        'no_product_link_message': 'No more information',
        'incorrect_storage_volume_message': 'Enter liters count, please',

        'vega_base_button': 'Vega base',
        'bloom_base_button': 'Bloom base',
        'targets_button': 'Additives',
        'different_products_button': 'For different products',

        'add_product_button': 'In table +',
        'remove_product_button': 'Remove -',
        'product_link_button': 'More',

        'edit_products_button': 'Edit',

        'download_xls_button': 'Download xls',
        'download_calendar_button️': 'Add to calendar',
    }
}
messages['ru'].update(ru_home_buttons)
messages['en'].update(en_home_buttons)


def get_message(message_name: str, lang: str):
    assert lang.lower() == ENGLISH or lang.lower() == RUSSIAN
    try:
        return messages[lang.lower()][message_name]
    except KeyError:
        return message_name


def is_button(text: str, button_key_name: str):
    """Is the given text the button_key_name value"""
    assert button_key_name in ru_home_buttons or button_key_name in en_home_buttons
    return text in ru_home_buttons[button_key_name] or text in en_home_buttons[button_key_name]


def get_all_messages(lang_code: str = DEFAULT_LANG):
    """Get all messages in the lang_code"""
    assert lang_code.lower() in messages.keys()
    return messages[lang_code.lower()]
