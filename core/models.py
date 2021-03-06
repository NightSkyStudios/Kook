import sys
from django.db import models
from django.dispatch import receiver
from django.db.models.signals import post_delete
from datetime import datetime
from core.google_calendar import create_event_from_booking, create_event_from_banquet
from django.conf import settings
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile


# Image compressor
def compressImage(uploadedImage):
    imageTemproary = Image.open(uploadedImage)
    outputIoStream = BytesIO()
    imageTemproaryResized = imageTemproary.resize((1020, 573))
    imageTemproary.save(outputIoStream,
                        format='JPEG',
                        quality=85)
    outputIoStream.seek(0)
    uploadedImage = InMemoryUploadedFile(outputIoStream,
                                         'ImageField',
                                         "%s.jpg" % uploadedImage.name.split('.')[0],
                                         'image/jpeg',
                                         sys.getsizeof(outputIoStream),
                                         None)
    return uploadedImage


class Promo(models.Model):
    """
    Model for promo codes
    """
    name = models.CharField('Код Промокоду',
                            max_length=60)
    discount = models.DecimalField('Значення промокоду',
                                   max_digits=3,
                                   decimal_places=0)
    is_percentage = models.BooleanField('Це відсоток?',
                                        default=True)
    date_expired = models.DateField('Дата закінчення',
                                    default=datetime.now)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоди'


class RoomType(models.Model):
    """
       Model for room types
    """
    image = models.ImageField(
        'Фото кімнати',
        upload_to='room_types',
        blank=True)
    name = models.CharField('Тип Кімнати',
                            max_length=64)
    quantity = models.IntegerField('Кількість кімнат')
    color_id = models.IntegerField('Id кольору')
    price = models.PositiveIntegerField('Ціна')
    description = models.TextField()

    def save(self, *args, **kwargs):
        if not self.id:
            self.image = compressImage(self.image)
        super(RoomType, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Тип Кімнати'
        verbose_name_plural = 'Типи Кімнат'


class Booking(models.Model):
    """
    Model for Booking
    """
    BED_TYPE_CHOICES = (
        ('Двохспальне ліжко', 'Двохспальне ліжко'),
        ('Два Односпальних ліжка', 'Два односпальних ліжка'),
    )

    pib = models.CharField('П.І.Б.',
                           max_length=225)
    phone = models.CharField(
        'Номер телефону',
        max_length=225,
        help_text='Контактний номер телефону')
    email = models.EmailField('E-mail')
    date_entry = models.DateField('Дата заїзду')
    date_leave = models.DateField('Дата виїзду')
    quantity = models.IntegerField('Кількість осіб')
    room_type = models.ForeignKey(RoomType,
                                  on_delete=models.CASCADE,
                                  verbose_name='Тип Кімнати')
    additional = models.CharField('Додаткові опціі',
                                  max_length=225,
                                  blank=True)
    breakfast = models.BooleanField('Сніданок',
                                    default=True)
    bed_type = models.CharField(
        'Тип Ліжка',
        default='Двохспальне ліжко',
        max_length=225,
        choices=BED_TYPE_CHOICES)
    notes = models.TextField(
        'Нотатки',
        blank=True,
        help_text='Цей текст буде бачити тільки адміністратор та модератор')
    is_paid = models.BooleanField('Оплата',default=False)
    discount = models.CharField(
        'Промокод', max_length=225, null=True, blank=True)
    price = models.PositiveIntegerField('Ціна', null=False, blank=True)

    # save event to google calendar + preload price
    def save(self, *args, **kwargs):
        day = self.date_leave - self.date_entry
        self.price = self.room_type.price * day.days

        super().save()
        if settings.ENABLE_GOOGLE_CALENDAR:
            create_event_from_booking(self)

    def __str__(self):
        template = '{0.pib} | {0.phone} | {0.room_type}'
        return template.format(self)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'


class MenuCategories(models.Model):
    """
         Model for menu categories
    """
    name = models.CharField('Назва Категорії',
                            max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категорія Страви'
        verbose_name_plural = 'Категорії Страв'


class MenuItem(models.Model):
    """
    Model for menu items
    """
    image = models.ImageField(
        'Зображення',
        blank=True,
        upload_to='menu_images')
    title = models.CharField('Назва страви',
                             max_length=24,
                             help_text='Максимум <b>24</b> символи')
    description = models.TextField('Опис',
                                   max_length=128,
                                   help_text='Максимум <b>128</b> символи')
    price = models.DecimalField('Ціна',
                                max_digits=5,
                                decimal_places=0)
    category = models.ManyToManyField(MenuCategories)

    def get_categories_class(self):
        res = ''
        for item in self.category.all():
            res += f'cat_{item.id} '
        return res

    def save(self, *args, **kwargs):
        if not self.id:
            self.image = compressImage(self.image)
        super(MenuItem, self).save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Страву'
        verbose_name_plural = 'Страви'


class Banquet(models.Model):
    """
         Model for Banquet Booking
    """
    check_in = models.DateField('Дата',
                                default=datetime.now)
    pib = models.CharField('П.І.Б.',
                           max_length=225)
    phone = models.CharField(
        'Номер телефону',
        max_length=225,
        help_text='Контактний номер телефону')
    email = models.EmailField('E-mail')
    notes = models.TextField(
        'Нотатки',
        blank=True,
        help_text='Цей текст буде бачити тільки адміністратор та модератор')

    def save(self, *args, **kwargs):
        super().save()
        if settings.ENABLE_GOOGLE_CALENDAR:
            create_event_from_banquet(self)

    def __str__(self):
        template = '{0.pib} | {0.phone}'
        return template.format(self)

    class Meta:
        verbose_name = 'Банкет'
        verbose_name_plural = 'Банкет'


class GalleryCategory(models.Model):
    """
         Model for gallery categories
    """
    name = models.CharField('Назіва категорії',
                            max_length=64)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Категорія Галереї'
        verbose_name_plural = 'Категорії галереї'


class GalleryPhoto(models.Model):
    """
         Model for gallery photos
    """
    GALLERY_CHOICES = (
        ('Ресторан', 'Ресторан'),
        ('Банкетний Зал', 'Банкетний Зал'),
        ('Готель', 'Готель'),
    )

    name = models.CharField('Назва',
                            max_length=255,
                            null=True,
                            blank=True,
                            help_text='Потрібно для відображення на комп\'ютерах зі слабким підключення до інтернету')
    image = models.ImageField('Зображення',
                              upload_to='img',
                              null=True,
                              blank=True,
                              )
    category = models.ManyToManyField(GalleryCategory)

    def save(self, *args, **kwargs):
        if not self.id:
            self.image = compressImage(self.image)
        super(GalleryPhoto, self).save(*args, **kwargs)

    def get_categories_class(self):
        res = ''
        for item in self.category.all():
            res += f'cat_{item.id} '
        return res

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Галерея'
        verbose_name_plural = 'Галерея'


class Slider(models.Model):
    """
         Model for slider photos
    """
    image = models.ImageField('Зображення',
                              upload_to='img',
                              null=True,
                              blank=True, )
    title = models.CharField('Верхній тект',
                             null=True,
                             blank=True,
                             max_length=64)
    sub_title = models.CharField('Нижній тект',
                                 null=True,
                                 blank=True,
                                 max_length=132)

    def __str__(self):
        template = '{0.title} | {0.sub_title}'
        return template.format(self)

    def save(self, *args, **kwargs):
        if not self.id:
            self.image = compressImage(self.image)
        super(Slider, self).save(*args, **kwargs)

    class Meta:
        verbose_name = 'Слайдер'
        verbose_name_plural = 'Слайдер'


# Delete photo if model.object delete
@receiver(post_delete)
def submission_delete(sender, instance, **kwargs):
    try:
        instance.image.delete(False)
    except AttributeError:
        pass
