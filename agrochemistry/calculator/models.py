from django.db import models


PRODUCT_ENVIRONMENTS = [
    ('universal', 'Универсальный'),
    ('hydro', 'Гидропоника'),
    ('terra', 'Земля'),
    ('coco', 'Кокос'),
    ('natural', 'Органическая'),
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


class Brand(models.Model):
    name = models.CharField('Название', max_length=20, db_index=True)

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'

    def __str__(self):
        return self.name


class ProductTarget(models.Model):
    tag = models.CharField('Название тэга', max_length=20)

    class Meta:
        verbose_name = 'Цель продукта'
        verbose_name_plural = 'Цели продуктов'

    def __str__(self):
        return self.tag


class Product(models.Model):
    brand = models.ForeignKey(Brand, verbose_name='Производитель', on_delete=models.CASCADE, related_name='products')
    name = models.CharField('Название', max_length=50, db_index=True)
    photo = models.ImageField('Фото', upload_to='product-photos/', blank=True, null=True)
    environment = models.CharField('Среда', choices=PRODUCT_ENVIRONMENTS, max_length=25)
    target = models.ForeignKey(ProductTarget, verbose_name='Цель', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    def __str__(self):
        return self.name


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
