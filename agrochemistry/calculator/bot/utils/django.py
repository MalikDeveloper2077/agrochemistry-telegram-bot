from calculator.models import TelegramUser


def get_user(username: str) -> TelegramUser:
    user, _ = TelegramUser.objects.get_or_create(username=username)
    return user


def set_user_language(user: TelegramUser, language: str):
    user.language = language
    user.save(update_fields=('language',))


def filter_user_last_query_products(user: TelegramUser, filter_arguments: dict):
    """Filter the last_query_products by the given arguments

    Parameters:
        user (TelegramUser): user which query products will be filtered
        filter_arguments (dict): Keys and values for the django filter function arguments
            {'filter_param1': value1, 'filter_param2': value2, ...}

    """
    user.last_query_products.remove(
        *[product for product in user.last_query_products.all() if product not in
          user.last_query_products.filter(**filter_arguments)]
    )
