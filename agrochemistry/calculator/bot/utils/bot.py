from os import remove as os_remove
from itertools import zip_longest
from typing import Union
from difflib import SequenceMatcher

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from agrochemistry.settings import translator
from calculator.bot.tabler import get_rendered_table_img_path, get_created_xls_table_path, get_created_calendar_file
from calculator.bot.utils.django import get_user
from calculator.bot.config import (HOME_BUTTON, CALCULATOR_BUTTON, RETURN_TO_QUERY_PRODUCTS, EDIT_USER_PRODUCTS,
                                   SHOW_MORE_QUERY_PRODUCTS, ADD_PRODUCT, REMOVE_PRODUCT, RETURN_TO_FILTERS,
                                   PRODUCT_DESCRIPTION_LINK_BUTTON, SEND_PRODUCT_LINK, SEND_TABLE_XLS, DEFAULT_LANG,
                                   ADD_PRODUCT_BUTTON, REMOVE_PRODUCT_BUTTON, SEND_CALENDAR_FILE)
from calculator.models import (TelegramUser, Product, ProductTarget, Brand, USER_LANGUAGES, PRODUCT_ENVIRONMENTS,
                               VEGA_BASE_CATEGORY, BLOOM_BASE_CATEGORY, USER_OS, ANDROID_OS)


def get_products_names(products):
    products_names = '\n☘️ '.join([product.name for product in products])
    return f"\n☘️ {products_names} "


def get_translated_text(text: str, lang: str):
    return translator.translate(text, dest=lang).text


def similar(first: str, second: str):
    return SequenceMatcher(None, first, second).ratio() > 0.6


def send_translated_message(send_func, lang: str, text: str, *args, **kwargs):
    """TODO"""
    send_func(text=get_translated_text(text, lang), *args, **kwargs)


def get_main_reply_keyboard(lang: str = DEFAULT_LANG, add_buttons=None) -> ReplyKeyboardMarkup:
    if add_buttons is None:
        add_buttons = []

    if add_buttons and lang != DEFAULT_LANG:
        translated_btns = []
        for btns in add_buttons:
            translated_btns.append([get_translated_text(btn, lang) for btn in btns])
        add_buttons = translated_btns

    home_btn = get_translated_text(HOME_BUTTON, lang)
    if add_buttons and len(add_buttons[-1]) == 1:
        add_buttons[-1].insert(0, home_btn)
    else:
        add_buttons.append([home_btn])

    return ReplyKeyboardMarkup(add_buttons)


def get_lists_separated_by_2_elements(lst: list):
    """Returns: [[elem1, elem2], [elem3, elem4], ...]"""
    iterables = [iter(lst)] * 2
    lst = [*zip_longest(*iterables)]
    if lst[-1][-1] is None:
        lst[-1] = lst[-1][:-1]  # remove None value in the end
    return lst


def get_inline_markup_language_selection() -> InlineKeyboardMarkup:
    """Return the keyboard with the all languages separated by 2 in a line"""
    buttons = [InlineKeyboardButton(lang, callback_data=lang) for _, lang in USER_LANGUAGES]
    return InlineKeyboardMarkup(get_lists_separated_by_2_elements(buttons))


def get_product_environment_reply_keyboard() -> ReplyKeyboardMarkup:
    environments = [env for env, _ in PRODUCT_ENVIRONMENTS]
    return ReplyKeyboardMarkup(get_lists_separated_by_2_elements(environments))


def get_targets_inline_markup(environment: str, lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
    """TODO"""
    assert environment in [env_val for env_val, env_name in PRODUCT_ENVIRONMENTS]
    buttons = [
        InlineKeyboardButton(
            f'{get_translated_text(target.tag, lang)}'
            f'({target.products.filter(environment=environment).count()})',
            callback_data=target.id
        )
        for target in ProductTarget.objects.all()
    ]
    return InlineKeyboardMarkup(get_lists_separated_by_2_elements(buttons))


def get_product_inline_markup(product_id, return_btn=False, next_products_count=0, action=ADD_PRODUCT,
                              is_user_product: bool = False, lang: str = DEFAULT_LANG):
    """Add to the end of function name product id.
    If you use continue_btn you should use continue_count as well
    """
    if action == ADD_PRODUCT:
        action_button_text = get_translated_text(ADD_PRODUCT_BUTTON, lang)
    elif action == REMOVE_PRODUCT:
        action_button_text = get_translated_text(REMOVE_PRODUCT_BUTTON, lang)
    else:
        raise ValueError('Incorrect action arg')

    buttons = [
        [
            InlineKeyboardButton(
                action_button_text,
                callback_data=f'{action} {int(product_id)} {return_btn or ""} {next_products_count or ""}'
            ),
            InlineKeyboardButton(
                f'{get_translated_text(PRODUCT_DESCRIPTION_LINK_BUTTON, lang)}',
                callback_data=f'{SEND_PRODUCT_LINK} {product_id}'
            )
        ],
    ]

    buttons_to_add = []
    if return_btn:
        buttons_to_add.append(InlineKeyboardButton('⬅️', callback_data=f'{RETURN_TO_FILTERS}'))

    if next_products_count:
        buttons_to_add.append(InlineKeyboardButton(
            f'⬇️ ({next_products_count})',
            callback_data=f'{SHOW_MORE_QUERY_PRODUCTS} {product_id} {is_user_product}'
        ))

    if buttons_to_add:
        buttons.append(buttons_to_add)

    return InlineKeyboardMarkup(buttons)


def get_filters_inline_markup(lang: str = DEFAULT_LANG):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_translated_text('База вега', lang),
                callback_data=f'filter_by_base_category {VEGA_BASE_CATEGORY}'
            ),
            InlineKeyboardButton(
                get_translated_text('База цветение', lang),
                callback_data=f'filter_by_base_category {BLOOM_BASE_CATEGORY}'
            )
        ],
        [
            InlineKeyboardButton(
                get_translated_text('Добавки', lang),
                callback_data='targets_list'
            ),
            InlineKeyboardButton(
                get_translated_text('Для разных растений', lang),
                callback_data='iaborov'
            )
        ]
    ])


def get_checkout_inline_markup(lang: str = DEFAULT_LANG):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('⬅️', callback_data=RETURN_TO_QUERY_PRODUCTS),
            InlineKeyboardButton(get_translated_text('Править', lang), callback_data=EDIT_USER_PRODUCTS)
        ]
    ])


def get_table_inline_markup(lang: str = DEFAULT_LANG):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_translated_text('Скачать xls', lang), callback_data=SEND_TABLE_XLS),
            InlineKeyboardButton(
                get_translated_text('Добавить в календарь️', lang),
                callback_data=SEND_CALENDAR_FILE
            ),
        ],
        [
            InlineKeyboardButton('⬅️', callback_data=RETURN_TO_QUERY_PRODUCTS),
        ]
    ])


def get_os_selecting_inline_markup():
    return InlineKeyboardMarkup(get_lists_separated_by_2_elements(
        [InlineKeyboardButton(os, callback_data=os) for os, _ in USER_OS]
    ))


def get_filtered_products_message(products, property_name: str, values: Union[list, set], title_prefix: str = ''):
    """TODO:"""
    msg = ''
    for val in values:
        if not val:
            continue

        if title_prefix:
            title_prefix += ' '

        msg += f'<i>{title_prefix}{val}</i>\n'

        filtered_products = products.filter(**{property_name: val}).values_list('brand__name', 'name')
        for brand_name, product_name in filtered_products:
            msg += f'{brand_name} - {product_name}\n'
    return msg


def get_checkout_message_text(products):
    """TODO:
    USES HTML!
    """
    environments = set(list(products.values_list('environment', flat=True)))
    message = ''
    for env in environments:
        message += f'<b>{env}</b>\n--------\n'
        env_products = products.filter(environment=env)

        base_categories = set(list(env_products.values_list('base_category', flat=True)))
        message += get_filtered_products_message(env_products, 'base_category', base_categories, 'База')

        targets = set(list(env_products.values_list('target__tag', flat=True)))
        message += get_filtered_products_message(env_products, 'target__tag', targets)

        message += '\n'

    return message


def get_next_products_count(products_count: int):
    """TODO"""
    if products_count >= 5:
        return products_count - 5
    return 0


def get_product_button_action(product_id: int, user_products):
    """TODO"""
    if user_products.filter(id=product_id).exists():
        return REMOVE_PRODUCT
    return ADD_PRODUCT


def send_filters(bot: CallbackContext.bot, chat_id: int, lang: str = DEFAULT_LANG):
    """Send filters for base category, targets as inline markup.
    Set the main reply markup with 'Калькулятор' button.
    """
    bot.send_message(
        chat_id=chat_id,
        text='👍',
        reply_markup=get_main_reply_keyboard(add_buttons=[[CALCULATOR_BUTTON]], lang=lang)
    )

    msg = 'Выберите название бренда или продолжайте выбор'
    if lang != DEFAULT_LANG:
        send_translated_message(
            send_func=bot.send_message,
            lang=lang,
            chat_id=chat_id,
            text=msg,
            reply_markup=get_filters_inline_markup(lang=lang)
        )
    else:
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=get_filters_inline_markup())


def send_product(product: Product, bot: CallbackContext.bot, chat_id: int,
                 markup: InlineKeyboardMarkup = None, button_action: str = ADD_PRODUCT,
                 is_user_product: bool = False, lang: str = DEFAULT_LANG):
    """Send the product with the action inline markup
    TODO"""
    message_text = f'{product.brand.name} - {product.name}'
    if markup is None:
        markup = get_product_inline_markup(product.id, action=button_action, is_user_product=is_user_product, lang=lang)

    if product.photo:
        bot.send_photo(
            chat_id=chat_id,
            photo=product.photo,
            caption=message_text,
            reply_markup=markup
        )
    else:
        bot.send_message(
            chat_id=chat_id,
            text=message_text,
            reply_markup=markup
        )


def send_products(products, bot: CallbackContext.bot, chat_id: int, user_products,
                  next_products_count: int = 0, is_user_products: bool = False, lang: str = DEFAULT_LANG):
    """TODO:"""
    products = list(products)
    if not len(products):
        return

    if len(products) == 1:
        btn_action = get_product_button_action(product_id=products[0].id, user_products=user_products)
        send_product(products[0], bot, chat_id, markup=get_product_inline_markup(
            product_id=products[0].id, return_btn=True, action=btn_action, is_user_product=is_user_products, lang=lang
        ))
        return

    for product in products[:-1]:
        btn_action = get_product_button_action(product_id=product.id, user_products=user_products)
        send_product(product, bot, chat_id, button_action=btn_action, is_user_product=is_user_products, lang=lang)

    last_product = products[-1]
    send_product(last_product, bot, chat_id, get_product_inline_markup(
        product_id=last_product.id,
        return_btn=True,
        next_products_count=next_products_count,
        action=get_product_button_action(product_id=last_product.id, user_products=user_products),
        is_user_product=is_user_products,
        lang=lang
    ))


def send_checkout(bot: CallbackContext.bot, chat_id: int, products, lang: str = DEFAULT_LANG):
    """TODO:"""
    message_text = get_checkout_message_text(products)
    markup = get_checkout_inline_markup(lang)
    bot.send_message(chat_id=chat_id, text=message_text, reply_markup=markup, parse_mode=ParseMode.HTML)


def send_table(bot: CallbackContext.bot, chat_id: int, user: TelegramUser, lang: str = DEFAULT_LANG):
    """TODO"""
    msg = 'Ваша таблица почти готова...'
    markup = get_main_reply_keyboard()
    if lang != DEFAULT_LANG:
        send_translated_message(send_func=bot.send_message, lang=lang, chat_id=chat_id, text=msg,
                                reply_markup=markup)
    else:
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=markup)

    table_img_path = get_rendered_table_img_path(user.products.all(), user.storage_volume)
    bot.send_photo(chat_id, open(table_img_path, 'rb'), reply_markup=get_table_inline_markup(lang=lang))
    os_remove(table_img_path)


def send_table_xls(bot: CallbackContext.bot, chat_id: int, username: str):
    """TODO"""
    user = get_user(username)

    table_xls_path = get_created_xls_table_path(user.products.all(), user.storage_volume)
    with open(table_xls_path, 'rb') as table:
        bot.send_document(chat_id=chat_id, filename=table_xls_path, document=table)

    os_remove(table_xls_path)
    return 12


def send_calendar_file(bot: CallbackContext.bot, chat_id: int, username: str, start_date: str):
    user = get_user(username)
    table_calendar_path = get_created_calendar_file(user.products.all(), user.storage_volume, start_date)

    with open(table_calendar_path, 'rb') as table:
        bot.send_document(chat_id=chat_id, filename=table_calendar_path, document=table)

    os_remove(table_calendar_path)
    return 12
