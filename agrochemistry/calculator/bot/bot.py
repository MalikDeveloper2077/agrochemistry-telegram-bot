from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler, CallbackContext
from telegram import Update, ReplyKeyboardRemove

import calculator.bot.config as config
from calculator.models import Product, TelegramUser, PRODUCT_ENVIRONMENTS, ProductTarget, Brand

from .messages import ru_home_buttons, en_home_buttons, is_button
from .utils.django import get_user, set_user_language, filter_user_last_query_products
from .utils import bot as bot_utils
from .keyboards import *


def start(update, _):
    """Start command. Send the inline keyboard to select a language.
    If a user already selected a language, send the message for environment selecting
    """
    user = get_user(update.message.from_user.username)
    if not user.language:
        update.message.reply_text(text='Привет / hi', reply_markup=ReplyKeyboardRemove())
        update.message.reply_text(text='👇', reply_markup=get_inline_markup_language_selection())
        return 1

    markup = get_product_environment_reply_keyboard()
    bot_utils.send_translated_message(
        send_func=update.message.reply_text,
        lang=user.language,
        message_name='environment_message',
        reply_markup=markup
    )
    return 2


def stop(update, _=None):
    """Stop command. Clear the user data"""
    user = get_user(update.message.from_user.username)
    bot_utils.send_translated_message(
        send_func=update.message.reply_text,
        lang=user.language,
        message_name='stop_message',
        reply_markup=ReplyKeyboardRemove()
    )
    user.clear()
    return ConversationHandler.END


def language_selecting_callback(update: Update, context: CallbackContext):
    """Set the user language from callback data.
    Send product environments to select
    """
    user = get_user(update.callback_query.message.chat.username)
    set_user_language(user, update.callback_query.data)

    markup = get_product_environment_reply_keyboard()
    bot_utils.send_translated_message(
        send_func=context.bot.send_message,
        lang=user.language,
        message_name='environment_message',
        chat_id=update.effective_message.chat_id,
        reply_markup=markup
    )
    return 2


def environment_selecting(update: Update, context: CallbackContext):
    """Filter the user last query products by environment and send the filters"""
    user = get_user(update.message.from_user.username)
    selected_environment = update.message.text

    if selected_environment not in [env for env, val in PRODUCT_ENVIRONMENTS]:
        envs_markup = get_product_environment_reply_keyboard()
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
    """Handle filter stage callback data by calling the method"""
    return handle_additional_handlers(update=update, bot=context.bot)


def target_selecting_response(bot: CallbackContext.bot, chat_id: int, username: str):
    """Send products targets with the user query products environment"""
    user = get_user(username)
    selected_environment = user.last_query_products.first().environment
    bot_utils.send_translated_message(
        send_func=bot.send_message,
        lang=user.language,
        chat_id=chat_id,
        message_name='target_message',
        reply_markup=get_targets_inline_markup(selected_environment, lang=user.language)
    )
    return 7


def target_selecting_callback(update: Update, context: CallbackContext):
    """Filter by the callback target and send the query products"""
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
        product_description_link = get_message('no_product_link_message', lang=lang)
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
    """Handler of main reply keyboard buttons"""
    msg = update.message.text

    if is_button(msg, 'home_button'):
        stop(update)
        return ConversationHandler.END

    user = get_user(update.message.from_user.username)

    if is_button(msg, 'send_table_button'):
        bot_utils.send_translated_message(send_func=update.message.reply_text,
                                          message_name='storage_volume_message', lang=user.language)
        return 11

    elif is_button(msg, 'calculator_button'):
        user_products = user.products.all()
        if not user_products:
            bot_utils.send_translated_message(send_func=update.message.reply_text,
                                              message_name='no_user_products_message', lang=user.language)
            bot_utils.send_filters(bot=context.bot, chat_id=update.effective_message.chat_id, lang=user.language)
            return 5

        send_table_btn = get_message('send_table_button', lang=user.language)
        reply_markup = get_main_reply_keyboard(add_buttons=[[send_table_btn]])
        bot_utils.send_translated_message(send_func=update.message.reply_text, lang=user.language,
                                          message_name='checkout_message', reply_markup=reply_markup)
        bot_utils.send_checkout(
            bot=context.bot,
            products=user_products,
            chat_id=update.effective_message.chat_id,
            lang=user.language
        )
        return 10


def table_callback(update: Update, context: CallbackContext):
    """The table keyboard buttons handler"""
    return handle_additional_handlers(update, context.bot)


def return_to_query_products_response(bot: CallbackContext.bot, chat_id: int, username: str):
    user = get_user(username)
    products = user.last_query_products.all()
    main_markup = get_main_reply_keyboard(add_buttons=[['calculator_button']], lang=user.language)

    bot_utils.send_translated_message(
        send_func=bot.send_message,
        lang=user.language,
        chat_id=chat_id,
        message_name='continue_products_selecting_message',
        reply_markup=main_markup
    )

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
    """Handler for the product keyboard buttons"""
    query = update.callback_query
    user = get_user(update.effective_user.username)

    if query.data.startswith(config.ADD_PRODUCT) or query.data.startswith(config.REMOVE_PRODUCT):
        args = query.data.split(' ')
        action = args.pop(0)  # remove config.ADD_PRODUCT or config.REMOVE_PRODUCT
        product_id = int(args[0])

        if action == config.ADD_PRODUCT:
            user.products.add(Product.objects.get(id=product_id))
            args.append(config.REMOVE_PRODUCT)
        elif action == config.REMOVE_PRODUCT:
            user.products.remove(Product.objects.get(id=product_id))
            args.append(config.ADD_PRODUCT)
        query.edit_message_reply_markup(reply_markup=get_product_inline_markup(*args, lang=user.language))

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
        start_index, end_index = bot_utils.get_next_five_products_indexes(products, clicked_product)

        next_products_to_show = products[start_index:end_index]
        bot_utils.send_products(
            products=next_products_to_show,
            user_products=user.products.all(),
            next_products_count=products.count() - end_index,
            bot=context.bot,
            chat_id=update.effective_message.chat_id,
            lang=user.language
        )
    return 9


def edit_user_products_response(bot: CallbackContext.bot, chat_id: int, username: str):
    """Handler to edit button. Send all user products"""
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
    """Handle the checkout keyboard callback data"""
    return handle_additional_handlers(update=update, bot=context.bot)


def storage_volume_selecting(update: Update, context: CallbackContext):
    """Handle for an entered user storage volume.
    Save the storage volume to user and send the table
    """
    user = get_user(update.message.from_user.username)
    try:
        volume = ''.join(symb for symb in update.message.text if symb.isdigit())
        assert volume != ''
    except AssertionError:
        bot_utils.send_translated_message(
            send_func=update.message.reply_text,
            lang=user.language,
            message_name='incorrect_storage_volume_message',
            reply_markup=ReplyKeyboardRemove()
        )
        return 11

    user.storage_volume = int(volume)
    user.save(update_fields=('storage_volume',))
    bot_utils.send_table(context.bot, update.effective_message.chat_id, user, lang=user.language)
    return 12


def message_handler(update: Update, context: CallbackContext):
    """Handle all unregistered messages (not command, not conversation answer).
    And the main keyboard buttons. Find products by the message text
    """
    msg = update.message.text
    user = get_user(update.effective_message.from_user.username)

    # If the message is a main keyboard button
    if msg in ru_home_buttons.values() or msg in en_home_buttons.values():
        return main_reply_keyboard_response(update, context)

    # Find a product or all brand products by comparing with the message text
    brand_products = Product.objects.filter(brand__name__icontains=msg)
    find_products = Product.objects.filter(name__icontains=msg)
    products = brand_products or find_products

    if not products:
        bot_utils.send_translated_message(send_func=update.message.reply_text, lang=user.language,
                                          message_name='no_searched_products_message')
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
    """Send OS selecting message"""
    user = get_user(username)
    markup = get_os_selecting_inline_markup()
    bot_utils.send_translated_message(send_func=bot.send_message, chat_id=chat_id,
                                      message_name='os_message', reply_markup=markup, lang=user.language)
    return 13


def os_selecting_callback(update: Update, context: CallbackContext):
    """Save if the selected OS is iOS. Send start cycle date message"""
    user = get_user(update.callback_query.message.chat.username)
    user.is_ios = update.callback_query.data == config.IOS
    user.save(update_fields=('is_ios',))

    chat_id = update.effective_message.chat_id
    bot_utils.send_translated_message(send_func=context.bot.send_message, chat_id=chat_id,
                                      message_name='start_cycle_date_message', lang=user.language)
    return 14


def calendar_start_date_selecting(update: Update, context: CallbackContext):
    """Save start cycle date to user.
    If the OS is iOS ask for user email
    Else send the .ics table file with the instructions
    """
    user = get_user(update.message.from_user.username)
    user.cycle_start_date = update.message.text
    user.save(update_fields=('cycle_start_date',))

    if user.is_ios:
        bot_utils.send_translated_message(update.message.reply_text, message_name='email_message',
                                          lang=user.language)
        return 15

    chat_id = update.effective_message.chat_id
    bot_utils.send_calendar_file(context.bot, chat_id, user.username, start_date=user.cycle_start_date)
    bot_utils.send_translated_message(send_func=update.message.reply_text, lang=user.language,
                                      message_name='calendar_instructions_message')
    return ConversationHandler.END


def email_selecting_response(update: Update, _):
    """Send the .ics calendar file to the user email and the instructions"""
    user_lang = get_user(update.message.from_user.username).language
    email = update.message.text
    try:
        bot_utils.send_email_calendar(username=update.message.from_user.username, to_email=(email,))
    except ValueError as e:
        # Incorrect start cycle date
        bot_utils.send_translated_message(send_func=update.message.reply_text, message_name=str(e), lang=user_lang)
        return 12

    bot_utils.send_translated_message(send_func=update.message.reply_text, lang=user_lang,
                                      message_name='ios_calendar_instructions_message')
    return ConversationHandler.END


def handle_additional_handlers(update: Update, bot: CallbackContext.bot):
    """Compare a callback data with the additional handlers method, call it"""
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
    # Additional methods to handle callback data from inline keyboards
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
        MessageHandler(Filters.text, message_handler)
    ]
)


def get_updater(token: str):
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conversation_handler)
    return updater
