from django.db import models
from phone_field import PhoneField
from django.dispatch import receiver
from django.db.models.signals import post_delete
from datetime import datetime


# Create your models here.

class Booking(models.Model):
    """
    Boking model
    """
    ROOM_CHOICES = (
        ('Стандарт', 'Стандарт'),
        ('Комфорт', 'Комфорт'),
        ('Комфорт Плюс', 'Комфорт Плюс'),
        ('Люкс', 'Люкс'),
        ('Тріо', 'Тріо')
    )

    pib = models.CharField('П.І.Б.', max_length=225)
    phone = models.CharField('Номер телефону', max_length=225, help_text='Контактний номер телефону')
    email = models.EmailField('E-mail')
    date_entry = models.DateField('Дата заїзду', default=datetime.now)
    date_leave = models.DateField('Дата виїзду', default=datetime.now)
    quantity = models.IntegerField('Кількість осіб')
    room_type = models.CharField('Тип Кімнати', max_length=225, choices=ROOM_CHOICES)
    additional = models.CharField('Додаткові опціі', max_length=225)
    breakfest = models.BooleanField('Сніданок', default=True)

    def __str__(self):
        template = '{0.pib} | {0.phone} | {0.room_type}'
        return template.format(self)

    class Meta:
        verbose_name = 'Замовлення'
        verbose_name_plural = 'Замовлення'


class MenuItem(models.Model):
    """
    Model for menu items
    """
    image = models.ImageField('Зображення', blank=True, upload_to='menu_images')
    title = models.CharField('Назва страви', max_length=225)
    description = models.TextField('Опис')
    price = models.IntegerField('Ціна')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукти'


@receiver(post_delete)
def submission_delete(sender, instance, **kwargs):
    try:
        instance.image.delete(False)
    except AttributeError:
        pass
