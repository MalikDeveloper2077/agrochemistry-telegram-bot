from itertools import zip_longest

from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton

from .messages import get_message
from calculator.models import (PRODUCT_ENVIRONMENTS, ProductTarget, VEGA_BASE_CATEGORY,
                               BLOOM_BASE_CATEGORY, USER_LANGUAGES)
from .config import (DEFAULT_LANG, ADD_PRODUCT, REMOVE_PRODUCT, SEND_PRODUCT_LINK,
                     RETURN_TO_FILTERS, SHOW_MORE_QUERY_PRODUCTS, RETURN_TO_QUERY_PRODUCTS,
                     EDIT_USER_PRODUCTS, SEND_TABLE_XLS, SEND_CALENDAR_FILE, IOS)


def get_lists_separated_by_2_elements(lst: list):
    """Returns: [[elem1, elem2], [elem3, elem4], ...]"""
    iterables = [iter(lst)] * 2
    lst = [*zip_longest(*iterables)]
    if lst[-1][-1] is None:
        lst[-1] = lst[-1][:-1]  # remove None value in the end
    return lst


def get_main_reply_keyboard(lang: str = DEFAULT_LANG, add_buttons=None) -> ReplyKeyboardMarkup:
    """Main reply keyboard.
    Contains the home button at the bottom/bottom & left of all buttons.

    Params:
        add_buttons (list): buttons to add to the keyboard. Example: [[button], [button2]]

    """
    if add_buttons is None:
        add_buttons = []

    if add_buttons and lang != DEFAULT_LANG:
        translated_btns = []
        for btns in add_buttons:
            translated_btns.append([get_message(btn, lang) for btn in btns])
        add_buttons = translated_btns

    home_btn = get_message('home_button', lang)
    if add_buttons and len(add_buttons[-1]) == 1:
        add_buttons[-1].insert(0, home_btn)
    else:
        add_buttons.append([home_btn])

    return ReplyKeyboardMarkup(add_buttons)


def get_inline_markup_language_selection() -> InlineKeyboardMarkup:
    """Return the keyboard with the all languages separated by 2 in a line"""
    buttons = [InlineKeyboardButton(lang, callback_data=lang) for _, lang in USER_LANGUAGES]
    return InlineKeyboardMarkup(get_lists_separated_by_2_elements(buttons))


def get_product_environment_reply_keyboard() -> ReplyKeyboardMarkup:
    """Return the keyboard with the all product environments separated by 2 in a line"""
    environments = [env for env, _ in PRODUCT_ENVIRONMENTS]
    return ReplyKeyboardMarkup(get_lists_separated_by_2_elements(environments))


def get_targets_inline_markup(environment: str, lang: str = DEFAULT_LANG) -> InlineKeyboardMarkup:
    """Return the keyboard with the all product targets separated by 2 in a line"""
    assert environment in [env_val for env_val, env_name in PRODUCT_ENVIRONMENTS]
    buttons = [
        InlineKeyboardButton(
            f'{get_message(target.tag, lang)}'
            f'({target.products.filter(environment=environment).count()})',
            callback_data=target.id
        )
        for target in ProductTarget.objects.all()
    ]
    return InlineKeyboardMarkup(get_lists_separated_by_2_elements(buttons))


def get_product_inline_markup(product_id, return_btn=False, next_products_count=0, action=ADD_PRODUCT,
                              is_user_product: bool = False, lang: str = DEFAULT_LANG):
    """Returns the product inline keyboard with 'Add/remove', 'More' buttons.

    Params:
        return_btn (bool): need a button for returning to the filters stage (⬅️)
        next_products_count (int, str): remaining products count. If it's not 0, add ⬇️ button and show the count there
        action (str): ADD_PRODUCT or REMOVE_PRODUCT
        is_user_product (bool): is product in the user selected products (user.products)

    """
    if action == ADD_PRODUCT:
        action_button_text = get_message('add_product_button', lang)
    elif action == REMOVE_PRODUCT:
        action_button_text = get_message('remove_product_button', lang)
    else:
        raise ValueError('Incorrect action arg')

    buttons = [
        [
            InlineKeyboardButton(
                action_button_text,
                # Callback data example: '{ADD_PRODUCT} 3 True 7':
                # 3 - product_id, True - need the return btn, 7 - next_products_count
                callback_data=f'{action} {int(product_id)} {return_btn or ""} {next_products_count or ""}'
            ),
            InlineKeyboardButton(
                f"{get_message('product_link_button', lang)}",
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

    if buttons_to_add:  # TODO: delete
        buttons.append(buttons_to_add)

    return InlineKeyboardMarkup(buttons)


def get_filters_inline_markup(lang: str = DEFAULT_LANG):
    """Return the filters inline keyboard with filter by product bases, targets"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                get_message('vega_base_button', lang),
                callback_data=f'filter_by_base_category {VEGA_BASE_CATEGORY}'
            ),
            InlineKeyboardButton(
                get_message('bloom_base_button', lang),
                callback_data=f'filter_by_base_category {BLOOM_BASE_CATEGORY}'
            )
        ],
        [
            InlineKeyboardButton(
                get_message('targets_button', lang),
                callback_data='targets_list'
            ),
            InlineKeyboardButton(
                get_message('different_products_button', lang),
                callback_data='iaborov'
            )
        ]
    ])


def get_checkout_inline_markup(lang: str = DEFAULT_LANG):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('⬅️', callback_data=RETURN_TO_QUERY_PRODUCTS),
            InlineKeyboardButton(get_message('edit_products_button', lang), callback_data=EDIT_USER_PRODUCTS)
        ]
    ])


def get_table_inline_markup(lang: str = DEFAULT_LANG):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_message('download_xls_button', lang), callback_data=SEND_TABLE_XLS),
            InlineKeyboardButton(
                get_message('download_calendar_button️', lang),
                callback_data=SEND_CALENDAR_FILE
            ),
        ],
        [
            InlineKeyboardButton('⬅️', callback_data=RETURN_TO_QUERY_PRODUCTS),
        ]
    ])


def get_os_selecting_inline_markup():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('iOS', callback_data=IOS),
        InlineKeyboardButton('Android/Windows/Mac/Linux', callback_data='not ios')
    ]])
