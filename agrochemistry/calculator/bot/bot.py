from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler, CallbackContext
from telegram import Update, ReplyKeyboardRemove

import calculator.bot.config as config
from calculator.models import Product, TelegramUser, PRODUCT_ENVIRONMENTS, ProductTarget, Brand, IOS_OS
from .utils.django import get_user, set_user_language, filter_user_last_query_products
from .utils import bot as bot_utils


def start(update, _):
    """Start step or catch all unregistered by other handlers messages.
    Send the inline keyboard to select a language
    """
    user = get_user(update.message.from_user.username)
    if not user.language:
        update.message.reply_text(text='Привет / hi', reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(text='👇', reply_markup=bot_utils.get_inline_markup_language_selection())
        return 1

    markup = bot_utils.get_product_environment_reply_keyboard()
    bot_utils.send_translated_message(
        send_func=update.message.reply_text,
        lang=user.language,
        text='Выберите среду выращивания',
        reply_markup=markup
    )
    return 2


def stop(update, _=None):
    user = get_user(update.message.from_user.username)
    bot_utils.send_translated_message(
        send_func=update.message.reply_text,
        lang=user.language,
        text=config.BOT_STOP_MESSAGE,
        reply_markup=ReplyKeyboardRemove()
    )
    user.clear()
    return ConversationHandler.END


def language_selecting_callback(update: Update, context: CallbackContext):
    """Set the user language from callback data.
    send product environments to select
    """
    user = get_user(update.callback_query.message.chat.username)
    set_user_language(user, update.callback_query.data)

    markup = bot_utils.get_product_environment_reply_keyboard()
    bot_utils.send_translated_message(
        send_func=context.bot.send_message,
        lang=user.language,
        text='Выберите среду выращивания',
        chat_id=update.effective_message.chat_id,
        reply_markup=markup
    )
    return 2


def environment_selecting(update: Update, context: CallbackContext):
    """Filter the user products by environment and send the brands list"""
    user = get_user(update.message.from_user.username)
    selected_environment = update.message.text

    if selected_environment not in [env for env, val in PRODUCT_ENVIRONMENTS]:
        envs_markup = bot_utils.get_product_environment_reply_keyboard()
        update.message.reply_text(config.INCORRECT_ENVIRONMENT_MESSAGE, reply_markup=envs_markup)
        return 2

    if not user.last_query_products.all():
        # Add all products to user query products for filtering in the future
        user.last_query_products.add(*Product.objects.all())

    filter_user_last_query_products(
        user=user,
        filter_arguments={'environment': selected_environment}
    )

    bot_utils.send_filters(bot=context.bot, chat_id=update.effective_message.chat_id, lang=user.language)
    return 5


def filter_selecting_callback(update: Update, context: CallbackContext):
    """TODO:"""
    return handle_additional_handlers(update=update, bot=context.bot)


def target_selecting_response(bot: CallbackContext.bot, chat_id: int, username: str):
    user = get_user(username)
    selected_environment = user.last_query_products.first().environment
    bot_utils.send_translated_message(
        send_func=bot.send_message,
        lang=user.language,
        chat_id=chat_id,
        text=f'Выберите категорию или отправьте название бренда/удобрения',
        reply_markup=bot_utils.get_targets_inline_markup(selected_environment, lang=user.language)
    )
    return 7


def target_selecting_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user = get_user(query.message.chat.username)
    try:
        filter_user_last_query_products(
            user=user,
            filter_arguments={'target': ProductTarget.objects.get(id=query.data)}
        )
    except ValueError:
        pass

    products = user.last_query_products.all()
    bot_utils.send_products(
        products=products[:5],
        user_products=user.products.all(),
        next_products_count=bot_utils.get_next_products_count(products.count()),
        bot=context.bot,
        chat_id=update.effective_message.chat_id,
        lang=user.language
    )
    return 9


def send_product_link_response(bot: CallbackContext.bot, chat_id: int, username: str, product_id: int):
    product_description_link = Product.objects.get(id=product_id).description_link
    if not product_description_link:
        lang = get_user(username).language
        product_description_link = bot_utils.get_translated_text(config.NO_PRODUCT_LINK_MESSAGE, lang=lang)
    bot.send_message(chat_id=chat_id, text=product_description_link)
    return 9


def filter_by_base_category_response(bot: CallbackContext.bot, chat_id: int, username: str, base_category: str):
    user = get_user(username)
    products = user.last_query_products.all()
    filter_user_last_query_products(
        user=user,
        filter_arguments={'base_category': base_category}
    )
    bot_utils.send_products(
        products=products[:5],
        user_products=user.products.all(),
        next_products_count=bot_utils.get_next_products_count(products.count()),
        chat_id=chat_id,
        bot=bot,
        lang=user.language
    )
    return 9


def main_reply_keyboard_response(update: Update, context: CallbackContext):
    """TODO: """
    if bot_utils.similar(bot_utils.get_translated_text(update.message.text, 'ru'), config.HOME_BUTTON):
        stop(update)
        return ConversationHandler.END

    user = get_user(update.message.from_user.username)

    if bot_utils.similar(bot_utils.get_translated_text(update.message.text, 'ru'), config.SEND_TABLE_BUTTON):
        bot_utils.send_translated_message(send_func=update.message.reply_text, text='Введите литраж',
                                          lang=user.language)
        return 11

    elif bot_utils.similar(bot_utils.get_translated_text(update.message.text, 'ru'), config.CALCULATOR_BUTTON):
        user_products = user.products.all()
        if not user_products:
            bot_utils.send_translated_message(send_func=update.message.reply_text, text='Вы еще ничего не добавили',
                                              lang=user.language)
            bot_utils.send_filters(bot=context.bot, chat_id=update.effective_message.chat_id, lang=user.language)
            return 5

        send_table_btn = bot_utils.get_translated_text(config.SEND_TABLE_BUTTON, lang=user.language)
        reply_markup = bot_utils.get_main_reply_keyboard(add_buttons=[[send_table_btn]])
        bot_utils.send_translated_message(send_func=update.message.reply_text, lang=user.language,
                                          text='Выбранные удобрения', reply_markup=reply_markup)
        bot_utils.send_checkout(
            bot=context.bot,
            products=user_products,
            chat_id=update.effective_message.chat_id,
            lang=user.language
        )
        return 10


def table_callback(update: Update, context: CallbackContext):
    return handle_additional_handlers(update, context.bot)


def return_to_query_products_response(bot: CallbackContext.bot, chat_id: int, username: str):
    """TODO:"""
    user = get_user(username)
    products = user.last_query_products.all()
    main_markup = bot_utils.get_main_reply_keyboard(add_buttons=[[config.CALCULATOR_BUTTON]], lang=user.language)

    msg = 'Продолжайте выбор'
    if user.language != config.DEFAULT_LANG:
        bot_utils.send_translated_message(
            send_func=bot.send_message,
            lang=user.language,
            chat_id=chat_id,
            text=msg,
            reply_markup=main_markup
        )
    else:
        bot.send_message(chat_id=chat_id, text=msg, reply_markup=bot_utils.get_main_reply_keyboard(
            add_buttons=[[config.CALCULATOR_BUTTON]]
        ))

    bot_utils.send_products(
        products=products[:5],
        user_products=user.products.all(),
        next_products_count=bot_utils.get_next_products_count(products.count()),
        bot=bot,
        chat_id=chat_id,
        lang=user.language
    )
    return 9


def product_callback(update: Update, context: CallbackContext):
    """TODO"""
    query = update.callback_query
    user = get_user(update.effective_user.username)

    if query.data.startswith(config.ADD_PRODUCT) or query.data.startswith(config.REMOVE_PRODUCT):
        args = query.data.split(' ')
        action = args.pop(0)  # remove config.ADD_PRODUCT
        product_id = int(args[0])
        if action == config.ADD_PRODUCT:
            user.products.add(Product.objects.get(id=product_id))
            args.append(config.REMOVE_PRODUCT)
        elif action == config.REMOVE_PRODUCT:
            user.products.remove(Product.objects.get(id=product_id))
            args.append(config.ADD_PRODUCT)
        query.edit_message_reply_markup(reply_markup=bot_utils.get_product_inline_markup(*args, lang=user.language))

    elif query.data.startswith(config.SEND_PRODUCT_LINK):
        product_id = int(query.data.split(' ')[1])
        chat_id = update.effective_message.chat_id
        send_product_link_response(bot=context.bot, chat_id=chat_id, username=user.username, product_id=product_id)

    elif query.data.startswith(config.RETURN_TO_FILTERS):
        bot_utils.send_filters(bot=context.bot, chat_id=update.effective_message.chat_id, lang=user.language)
        return 5

    elif query.data.startswith(config.SHOW_MORE_QUERY_PRODUCTS):
        if query.data.split(' ')[2] == 'True':
            products = user.products.all()
        else:
            products = user.last_query_products.all()

        clicked_product = Product.objects.get(id=query.data.split(' ')[1])
        clicked_product_index = list(products).index(clicked_product) + 1

        products_count = products.count()
        if products_count - clicked_product_index > 5:
            end_index = clicked_product_index + 5
        else:
            end_index = products_count

        next_products_to_show = products[clicked_product_index:end_index]
        remaining_products_count = products_count - end_index
        bot_utils.send_products(
            products=next_products_to_show,
            user_products=user.products.all(),
            next_products_count=remaining_products_count,
            bot=context.bot,
            chat_id=update.effective_message.chat_id,
            lang=user.language
        )
    return 9


def edit_user_products_response(bot: CallbackContext.bot, chat_id: int, username: str):
    user = get_user(username)
    products = user.products.all()
    bot_utils.send_products(
        products=products[:5],
        user_products=products,
        next_products_count=bot_utils.get_next_products_count(products.count()),
        bot=bot,
        chat_id=chat_id,
        is_user_products=True,
        lang=user.language
    )
    return 9


def checkout_response(update: Update, context: CallbackContext):
    """TODO:"""
    return handle_additional_handlers(update=update, bot=context.bot)


def storage_volume_selecting(update: Update, context: CallbackContext):
    """TODO"""
    user = get_user(update.message.from_user.username)
    try:
        volume = ''.join(symb for symb in update.message.text if symb.isdigit())
        assert volume != ''
    except AssertionError:
        bot_utils.send_translated_message(
            send_func=update.message.reply_text,
            lang=user.language,
            text=config.INCORRECT_STORAGE_VOLUME_MESSAGE,
            reply_markup=ReplyKeyboardRemove()
        )
        return 11

    user.storage_volume = int(volume)
    user.save(update_fields=('storage_volume',))
    bot_utils.send_table(context.bot, update.effective_message.chat_id, user, lang=user.language)
    return 12


def message_handler(update: Update, context: CallbackContext):
    """TODO:"""
    msg = update.message.text
    user = get_user(update.effective_message.from_user.username)

    # If the message is a main reply button but on another language
    for main_button in config.MAIN_KEYBOARD_BUTTONS:
        if bot_utils.similar(bot_utils.get_translated_text(msg, 'ru'), main_button):
            return main_reply_keyboard_response(update, context)

    brand_products = Product.objects.filter(brand__name__icontains=msg)
    find_products = Product.objects.filter(name__icontains=msg)
    products = brand_products or find_products

    if not products:
        bot_utils.send_translated_message(send_func=update.message.reply_text, lang=user.language,
                                          text=config.NO_SEARCHED_PRODUCTS_MESSAGE)
        bot_utils.send_filters(context.bot, update.effective_message.chat_id, lang=user.language)
        return 5

    bot_utils.send_products(
        products=products[:5],
        bot=context.bot,
        chat_id=update.effective_message.chat_id,
        user_products=user.products.all(),
        next_products_count=bot_utils.get_next_products_count(len(products)),
        lang=user.language
    )
    return 9


def os_selecting_response(bot: CallbackContext.bot, chat_id: int, username: str):
    user = get_user(username)
    markup = bot_utils.get_os_selecting_inline_markup()
    bot_utils.send_translated_message(send_func=bot.send_message, chat_id=chat_id,
                                      text=config.SELECT_OS_MESSAGE, reply_markup=markup, lang=user.language)
    return 13


def os_selecting_callback(update: Update, context: CallbackContext):
    user = get_user(update.callback_query.message.chat.username)
    user.os = update.callback_query.data
    user.save(update_fields=('os',))

    msg = 'Введите дату начала цикла (формат: yyyy-mm-dd)'
    chat_id = update.effective_message.chat_id
    bot_utils.send_translated_message(send_func=context.bot.send_message, chat_id=chat_id, text=msg, lang=user.language)
    return 14


def calendar_start_date_selecting(update: Update, context: CallbackContext):
    user = get_user(update.message.from_user.username)
    user.cycle_start_date = update.message.text
    user.save(update_fields=('cycle_start_date',))

    if user.os != IOS_OS:
        chat_id = update.effective_message.chat_id
        bot_utils.send_calendar_file(context.bot, chat_id, user.username, start_date=user.cycle_start_date)
        update.message.reply_text(config.CALENDAR_FILE_INSTRUCTIONS_MESSAGE)
        return ConversationHandler.END

    bot_utils.send_translated_message(update.message.reply_text, text=config.ENTER_EMAIL_MESSAGE, lang=user.language)
    return 15


def email_selecting_response(update: Update, context: CallbackContext):
    chat_id = update.effective_message.chat_id
    email = update.message.text
    user = get_user(update.message.from_user.username)
    bot_utils.send_calendar_file(context.bot, chat_id, user.username, start_date=user.cycle_start_date)
    update.message.reply_text(config.CALENDAR_FILE_IOS_INSTRUCTION_MESSAGE)
    return ConversationHandler.END


def handle_additional_handlers(update: Update, bot: CallbackContext.bot):
    """"""
    query = update.callback_query
    function_name = query.data.split(' ')[0]
    chat_id = update.effective_message.chat_id
    username = update.effective_user.username

    try:
        args = query.data.split(' ')[1:]
        return additional_handlers[function_name](bot, chat_id, username, *args)
    except IndexError:
        return additional_handlers[function_name](bot, chat_id, username)


additional_handlers = {
    # TODO:
    'targets_list': target_selecting_response,
    'send_product_link': send_product_link_response,
    'filter_by_base_category': filter_by_base_category_response,
    config.RETURN_TO_QUERY_PRODUCTS: return_to_query_products_response,
    config.EDIT_USER_PRODUCTS: edit_user_products_response,
    config.SEND_TABLE_XLS: bot_utils.send_table_xls,
    config.SEND_CALENDAR_FILE: os_selecting_response,
}

conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(Filters.text, start)],
    states={
        1: [CallbackQueryHandler(language_selecting_callback, pass_user_data=True)],
        2: [MessageHandler(Filters.text & ~Filters.command, environment_selecting, pass_user_data=True)],
        5: [CallbackQueryHandler(filter_selecting_callback, pass_user_data=True)],
        6: [CallbackQueryHandler(target_selecting_response, pass_user_data=True)],
        7: [CallbackQueryHandler(target_selecting_callback, pass_user_data=True)],
        9: [CallbackQueryHandler(product_callback, pass_user_data=True)],
        10: [CallbackQueryHandler(checkout_response, pass_user_data=True)],
        11: [MessageHandler(Filters.text & ~Filters.command, storage_volume_selecting, pass_user_data=True)],
        12: [CallbackQueryHandler(table_callback, pass_user_data=True)],
        13: [CallbackQueryHandler(os_selecting_callback, pass_user_data=True)],
        14: [MessageHandler(Filters.text & ~Filters.command, calendar_start_date_selecting, pass_user_data=True)],
        15: [MessageHandler(Filters.text & ~Filters.command, email_selecting_response, pass_user_data=True)]
    },
    fallbacks=[
        CommandHandler('stop', stop),
        MessageHandler(
            Filters.regex(bot_utils.get_translated_text(config.HOME_BUTTON, 'ru')) |
            Filters.regex(bot_utils.get_translated_text(config.CALCULATOR_BUTTON, 'ru')) |
            Filters.regex(bot_utils.get_translated_text(config.SEND_TABLE_BUTTON, 'ru')),
            main_reply_keyboard_response
        ),
        MessageHandler(Filters.text, message_handler)
    ]
)


def get_updater(token: str):
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conversation_handler)
    return updater
