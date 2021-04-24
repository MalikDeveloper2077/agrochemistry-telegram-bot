from os import remove as os_remove
from typing import Union

from telegram import InlineKeyboardMarkup, ParseMode
from telegram.ext import CallbackContext

from agrochemistry.settings import EMAIL_HOST_USER
from calculator.bot.utils.django import get_user
from calculator.bot.mailer import send_mail
from calculator.bot.messages import get_message, get_all_messages
from calculator.bot.table.tabler import (get_rendered_table_img_path, get_created_xls_table_path,
                                         get_created_calendar_file_path)
from calculator.bot.config import ADD_PRODUCT, REMOVE_PRODUCT, DEFAULT_LANG
from calculator.models import TelegramUser, Product
from calculator.bot.keyboards import get_main_reply_keyboard, get_product_inline_markup, \
    get_filters_inline_markup, get_checkout_inline_markup, get_table_inline_markup


def send_translated_message(send_func, lang: str, message_name: str, *args, **kwargs):
    """Send a message with the translated text.

    Parameters:
        send_func (function): a function to send message like bot.send_message or message.reply_text
        lang (str): lang in which the text will be translated
        message_name (str): message key. MUST BE in messages[lang] dict

    """
    assert message_name in get_all_messages(lang_code=DEFAULT_LANG).keys()
    send_func(text=get_message(message_name, lang), *args, **kwargs)


def get_filtered_products_message(products, property_name: str, values: Union[list, set],
                                  title_prefix: str = '') -> str:
    """Return a text with list of filtered products short descriptions separated by the values param

    Parameters:
        products (QuerySet): QS with Product objects
        property_name (str): field of a Product object to filter by
        values (list, set): all values for the filtering
        title_prefix (str): a text before the values names

    """
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


def get_checkout_message_text(products) -> str:
    """Return checkout message text (list of products separated by environments and bases with targets)
    CONTAINS HTML!
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
    """Count of remaining products after showing next 5"""
    if products_count >= 5:
        return products_count - 5
    return 0


def get_product_button_action(product_id: int, user_products) -> str:
    """Return ADD_PRODUCT or REMOVE_PRODUCT actions for interaction with the product: user adding or removing"""
    if user_products.filter(id=product_id).exists():
        return REMOVE_PRODUCT
    return ADD_PRODUCT


def get_next_five_products_indexes(products, last_product):
    products = list(products)
    start_index = products.index(last_product) + 1

    if len(products) - start_index > 5:
        end_index = start_index + 5
    else:
        end_index = len(products)
    return start_index, end_index


def send_filters(bot: CallbackContext.bot, chat_id: int, lang: str = DEFAULT_LANG):
    """Send filters for base category, targets as inline markup.
    Set the main reply markup with calculator button.
    """
    bot.send_message(
        chat_id=chat_id,
        text='👍',
        reply_markup=get_main_reply_keyboard(add_buttons=[['calculator_button']], lang=lang)
    )

    send_translated_message(
        send_func=bot.send_message,
        lang=lang,
        chat_id=chat_id,
        message_name='filters_message',
        reply_markup=get_filters_inline_markup(lang=lang)
    )


def send_product(product: Product, bot: CallbackContext.bot, chat_id: int,
                 markup: InlineKeyboardMarkup = None, button_action: str = ADD_PRODUCT,
                 is_user_product: bool = False, lang: str = DEFAULT_LANG):
    """Send the product data with the keyboard of get_product_inline_markup method
    Data: brand name, product name, ?photo

    Params:
        markup (InlineKeyboardMarkup): your own markup instead of the default
        button_action (str): add to user.products or remove, values: ADD_PRODUCT or REMOVE_PRODUCT
        is_user_product (bool): is the product added by a user (in user.products)

    """
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
    """Send the products with send_product method.
    If the count of products > 5, add for a last product custom keyboard
    with the return btn and next products count.

    Params:
        is_user_products (bool): is the products added by a user (in user.products)
        next_products_count (int, str): remaining products count (for ⬇️ button)

    """
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
    message_text = get_checkout_message_text(products)
    markup = get_checkout_inline_markup(lang)
    bot.send_message(chat_id=chat_id, text=message_text, reply_markup=markup, parse_mode=ParseMode.HTML)


def send_table(bot: CallbackContext.bot, chat_id: int, user: TelegramUser, lang: str = DEFAULT_LANG):
    """Send a table image with the inline keyboard. After sending remove from the files"""
    markup = get_main_reply_keyboard()
    send_translated_message(send_func=bot.send_message, lang=lang, chat_id=chat_id,
                            message_name='wait_for_table_message', reply_markup=markup)

    table_img_path = get_rendered_table_img_path(user.products.all(), user.storage_volume)
    bot.send_photo(chat_id, open(table_img_path, 'rb'), reply_markup=get_table_inline_markup(lang=lang))
    os_remove(table_img_path)


def send_table_xls(bot: CallbackContext.bot, chat_id: int, username: str):
    """Save table as xls file and send it. After sending remove from the files"""
    user = get_user(username)

    table_xls_path = get_created_xls_table_path(user.products.all(), user.storage_volume)
    with open(table_xls_path, 'rb') as table:
        bot.send_document(chat_id=chat_id, filename=table_xls_path, document=table)

    os_remove(table_xls_path)
    return 12


def send_calendar_file(bot: CallbackContext.bot, chat_id: int, username: str, start_date: str):
    """Save table as .ics file and send it. After sending remove from the files"""
    user = get_user(username)
    try:
        table_calendar_path = get_created_calendar_file_path(user.products.all(), user.storage_volume, start_date)
    except ValueError as e:
        # Incorrect the start cycle date
        send_translated_message(bot.send_message, chat_id=chat_id, message_name=str(e), lang=user.language)
        return 14

    with open(table_calendar_path, 'rb') as table:
        bot.send_document(chat_id=chat_id, filename=table_calendar_path, document=table)

    os_remove(table_calendar_path)
    return 12


def send_email_calendar(username: str, to_email: Union[tuple, list]):
    """Save table as .ics file and send it to the email.
    After sending remove from the files
    """
    user = get_user(username)
    calendar_path = get_created_calendar_file_path(
        products=user.products.all(),
        user_storage_volume=user.storage_volume,
        start_date=user.cycle_start_date
    )
    send_mail('Ваш файл календаря', sent_from=EMAIL_HOST_USER, to=to_email,
              subject='FstGrowerBot', attach_path=calendar_path)
    os_remove(calendar_path)
    return 12
