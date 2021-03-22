from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackQueryHandler, \
    CallbackContext
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, Update, ReplyKeyboardRemove

from calculator.models import Product, TelegramUser, PRODUCT_ENVIRONMENTS, ProductTarget


SKIP_QUESTION_TITLE = 'Пропустить'
SKIP_QUESTION_VALUE = 'skip'
CREATE_TABLE_TITLE = 'Сформировать таблицу'


def get_user(username):
    user, _ = TelegramUser.objects.get_or_create(username=username)
    return user


def clear_user(user):
    user.clear_products()
    user.clear_last_query_products()
    user.storage_volume = None
    user.save(update_fields=('storage_volume',))


def filter_user_last_query_products(user: TelegramUser, filter_arguments: dict):
    """filter_arguments (dict): Keys and values for the django filter function arguments
    {'filter_param1': value1, 'filter_param2': value2, ...}
    """
    user.last_query_products.remove(
        *[product for product in user.last_query_products.all() if product not in
          user.last_query_products.filter(**filter_arguments)]
    )


def get_products_names(products):
    products_names = '\n☘️ '.join([product.name for product in products])
    return f"\n☘️ {products_names} "


def message_handler(update, _):
    update.message.reply_text(text="Привет! Введи объём своего резервуара", reply_markup=ReplyKeyboardRemove())
    return 1


def stop(update, _):
    update.message.reply_text(text="Был рад помочь 🤗")
    clear_user(get_user(update.message.from_user.username))
    return ConversationHandler.END


def handle_callback_and_filter_query_products(query_data, user: TelegramUser, filter_arguments: dict):
    """filter_arguments (dict): Keys and values for the django filter function arguments
    {'filter_param1': value1, 'filter_param2': value2, ...}
    """
    if not query_data == SKIP_QUESTION_VALUE:
        filter_user_last_query_products(
            user,
            filter_arguments=filter_arguments
        )


def get_continue_searching_keyboard():
    buttons = [['Добавить ещё одно удобрение'], [CREATE_TABLE_TITLE]]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)


def get_inline_markup_with_skip_button(buttons):
    buttons.append([InlineKeyboardButton(SKIP_QUESTION_TITLE, callback_data=SKIP_QUESTION_VALUE)])
    return InlineKeyboardMarkup(buttons)


def first_response(update, _):
    user = get_user(update.message.from_user.username)

    if update.message.text == CREATE_TABLE_TITLE:
        clear_user(user)
        return ConversationHandler.END

    if not user.storage_volume:
        try:
            volume = ''.join(symb for symb in update.message.text if symb.isdigit())
            assert volume != ''

            user.storage_volume = volume
            user.save(update_fields=('storage_volume',))
        except AssertionError:
            update.message.reply_text('Пожалуйста, введите кол-во литров', reply_markup=ReplyKeyboardRemove())
            return 1

    update.message.reply_text('Введите название удобрения', reply_markup=ReplyKeyboardRemove())
    return 2


def second_response(update: Update, _):
    user = get_user(update.message.from_user.username)
    products = Product.objects.filter(name__icontains=update.message.text)
    user.last_query_products.add(*products)

    if products:
        if len(products) > 1:
            markup = get_inline_markup_with_skip_button(
                [[InlineKeyboardButton(env, callback_data=env_value)] for env_value, env in PRODUCT_ENVIRONMENTS]
            )
            update.message.reply_text('Выберите среду выращивания или пропустите этот этап', reply_markup=markup)
            return 3
        else:
            user.products.add(products[0])
            user_products = user.products.all()
            update.message.reply_text(
                f'Удобрение добавлено!\n\nВыбранные удобрения: '
                f'{get_products_names(user_products)}',
                reply_markup=get_continue_searching_keyboard()
            )

            # Send all selected products photos
            for product in user_products:
                if product.photo:
                    update.message.reply_photo(product.photo)

            return 1
    else:
        update.message.reply_text('Ничего не найдено\nПопробуйте найти что-то другое')
    return 2


def environment_response(update: Update, context: CallbackContext):
    query = update.callback_query
    handle_callback_and_filter_query_products(
        query_data=query.data,
        user=get_user(query.message.chat.username),
        filter_arguments={'environment': query.data}
    )

    markup = get_inline_markup_with_skip_button(
        [[InlineKeyboardButton(f'#{target.tag}', callback_data=target.id)]
         for target in ProductTarget.objects.all()]
    )
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text='Выберите основную цель удобрения или пропустите этот этап',
        reply_markup=markup
    )
    return 4


def target_response(update: Update, context: CallbackContext):
    query = update.callback_query
    user = get_user(query.message.chat.username)
    try:
        handle_callback_and_filter_query_products(
            query_data=query.data,
            user=user,
            filter_arguments={'target': ProductTarget.objects.get(id=query.data)}
        )
    except ValueError:
        pass

    last_query_products = user.last_query_products.all()
    chat_id = update.effective_message.chat_id
    if not last_query_products:
        context.bot.send_message(chat_id=chat_id, text='Ничего не найдено')
        return 1

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton(product.name, callback_data=product.id)] for product in last_query_products]
    )
    context.bot.send_message(
        chat_id=chat_id,
        text='Выберите удобрение',
        reply_markup=markup
    )
    return 5


def third_response(update: Update, context: CallbackContext):
    query = update.callback_query
    user = get_user(query.message.chat.username)
    user.products.add(Product.objects.get(id=query.data))
    context.bot.send_message(
        chat_id=update.effective_message.chat_id,
        text=f'Объём резервуара: {user.storage_volume} литров\n\n'
             f'Выбранные удобрения: {get_products_names(user.products.all())}',
        reply_markup=get_continue_searching_keyboard()
    )
    return 1


conversation_handler = ConversationHandler(
    entry_points=[MessageHandler(filters=Filters.all, callback=message_handler)],
    states={
        1: [MessageHandler(Filters.text, first_response, pass_user_data=True)],
        2: [MessageHandler(Filters.text, second_response, pass_user_data=True)],
        3: [CallbackQueryHandler(environment_response, pass_user_data=True)],
        4: [CallbackQueryHandler(target_response, pass_user_data=True)],
        5: [CallbackQueryHandler(third_response, pass_user_data=True)]
    },
    fallbacks=[CommandHandler('stop', stop)]
)


def get_updater(token: str):
    updater = Updater(token=token, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('stop', stop))
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_handler(CallbackQueryHandler(callback=third_response))
    dispatcher.add_handler(MessageHandler(filters=Filters.all, callback=message_handler))
    return updater
