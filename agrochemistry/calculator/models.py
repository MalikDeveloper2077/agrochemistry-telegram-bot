from django.core.exceptions import ValidationError
from django.db import models


PRODUCT_ENVIRONMENTS = [
    ('universal', 'Универсальный'),
    ('hydro', 'Гидропоника'),
    ('terra', 'Земля'),
    ('coco', 'Кокос'),
    ('natural', 'Органическая'),
]

VEGA_BASE_CATEGORY = 'vega'
BLOOM_BASE_CATEGORY = 'bloom'
PRODUCT_BASE_CATEGORIES = [
    ('vega', 'Вегетация'),
    ('bloom', 'Цветение')
]

PHASES = [
    ('start', 'Старт / Укоренение'),
    ('vegetative_first', 'Вегетативная фаза I'),
    ('vegetative_second', 'Вегетативная фаза II'),
    ('generative_first', 'Генеративный период I'),
    ('generative_second', 'Генеративный период II'),
    ('generative_third', 'Генеративный период III'),
    ('generative_fourth', 'Генеративный период IV'),
]

RUSSIAN_LANGUAGE = 'RU'
ENGLISH_LANGUAGE = 'EN'
USER_LANGUAGES = [
    (RUSSIAN_LANGUAGE, 'RU'),
    (ENGLISH_LANGUAGE, 'EN')
]

ANDROID_OS = 'android'
IOS_OS = 'ios'
MAC_OS = 'mac'
USER_OS = [
    (ANDROID_OS, ANDROID_OS),
    (IOS_OS, IOS_OS),
    (MAC_OS, MAC_OS)
]


class Brand(models.Model):
    name = models.CharField('Название', max_length=20, db_index=True)

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return self.name


class ProductTarget(models.Model):
    tag = models.CharField('Название тэга', max_length=20)
    color = models.CharField('Цвет в таблице (HEX)', max_length=10, blank=True)

    class Meta:
        verbose_name = 'Цель продукта'
        verbose_name_plural = 'Цели продуктов'

    def save(self, *args, **kwargs):
        if self.color:
            if not self.color.startswith('#'):
                self.color = f'#{self.color}'

        super().save(*args, **kwargs)

    def __str__(self):
        return self.tag


class Product(models.Model):
    brand = models.ForeignKey(Brand, verbose_name='Производитель', on_delete=models.CASCADE, related_name='products')
    name = models.CharField('Название', max_length=50, db_index=True)
    description_link = models.URLField('Ссылка на подробную информацию', blank=True)
    photo = models.ImageField('Фото', upload_to='product-photos/', blank=True, null=True)
    base_category = models.CharField('База', choices=PRODUCT_BASE_CATEGORIES, max_length=20, blank=True)
    environment = models.CharField('Среда', choices=PRODUCT_ENVIRONMENTS, max_length=25)
    target = models.ForeignKey(ProductTarget, verbose_name='Цель', related_name='products',
                               on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """Delete the photo after product deleting"""
        storage = self.photo.storage

        if storage.exists(self.photo.name):
            storage.delete(self.photo.name)

        super().delete()

    def save(self, *args, **kwargs):
        if self.base_category and self.target or not self.base_category and not self.target:
            raise ValidationError('Выберите либо базу либо цель удобрения')
        super().save(*args, **kwargs)

    @property
    def short_description(self):
        description = f'{self.brand.name} - {self.name}'
        try:
            description += f'\n{self.target.tag}'
        except AttributeError:
            # If product doesn't have a tag
            pass
        return description


class Phase(models.Model):
    product = models.ForeignKey(Product, verbose_name='Продукт', on_delete=models.CASCADE, related_name='phases')
    name = models.CharField('Название', choices=PHASES, max_length=40)
    description = models.CharField('Описание', max_length=200, blank=True)  # TODO: automatically set before creating
    weeks = models.CharField('Количество недель', max_length=10)
    formula = models.CharField('Формула', max_length=20, help_text='Пример: (r / 2) * 5, где r - объём резервуара')

    class Meta:
        verbose_name = 'Фаза'
        verbose_name_plural = 'Фазы'

    def __str__(self):
        return f'{self.product.name} | {self.name}'


class TelegramUser(models.Model):
    username = models.CharField('Юзернейм в телеграме', max_length=50, db_index=True, unique=True)
    storage_volume = models.SmallIntegerField('Объём резервуара', blank=True, null=True)
    products = models.ManyToManyField(Product, verbose_name='Продукты', related_name='users', blank=True)
    os = models.CharField('ОС', choices=USER_OS, max_length=10, blank=True)
    last_query_products = models.ManyToManyField(
        Product,
        related_name='users_from_query',
        verbose_name='Последние отфильтрованные продукты',
        blank=True
    )
    language = models.CharField(
        'Язык взаимодействия',
        choices=USER_LANGUAGES,
        max_length=6
    )
    cycle_start_date = models.CharField(
        'Дата начала цикла выращивания для календаря в ОС: yyyy-mm-dd',
        max_length=10,
        blank=True
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    def clear_products(self):
        self.products.clear()

    def clear_last_query_products(self):
        self.last_query_products.clear()

    def clear(self):
        self.clear_products()
        self.clear_last_query_products()
        self.storage_volume = None
        self.save(update_fields=('storage_volume',))
