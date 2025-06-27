from employees.models import Employees
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image, ExifTags


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    mobile_app = models.BooleanField(default=False, verbose_name='Мобильное приложение')
    delete_washorders = models.BooleanField(default=False, verbose_name='Может удалять заказы')
    delete_employees = models.BooleanField(default=False, verbose_name='Может удалять сотрудников')
    telegram_id = models.CharField(max_length=32, blank=True, null=True, verbose_name='Telegram ID')

    def __str__(self):
        return self.user.username


class TelegramUser(models.Model):
    telegram_id = models.CharField(max_length=32, unique=True, verbose_name='Telegram ID')
    username = models.CharField(max_length=255, blank=True, null=True, verbose_name='Username')
    first_name = models.CharField(max_length=255, blank=True, null=True, verbose_name='Имя')
    is_admin = models.BooleanField(default=False, verbose_name='Администратор')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'Telegram пользователь'
        verbose_name_plural = 'Telegram пользователи'

    def __str__(self):
        return f"{self.first_name or self.username or self.telegram_id} ({self.telegram_id})"


class Services(models.Model):
    name_services = models.CharField(max_length=200, verbose_name='Название услуги', unique=True)
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    def __str__(self):
        return self.name_services

    class Meta:
        verbose_name = 'Услугу'
        verbose_name_plural = 'Услуги'
        ordering = ['-time_create', 'name_services']


class ServiceClasses(models.Model):
    services = models.ForeignKey(Services, on_delete=models.CASCADE, verbose_name='Услуга')
    name = models.CharField(max_length=200, verbose_name='Название класса', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена класса', blank=True, null=True)
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    def __str__(self):
        return f"{self.services.name_services} - {self.name}"

    class Meta:
        verbose_name = 'Класс услуг'
        verbose_name_plural = 'Классы услуг'
        ordering = ['-time_create', 'name']


class WashOrders(models.Model):
    car_photo = models.ImageField(upload_to='car_photos/', verbose_name='Фото авто')
    type_of_car_wash = models.ForeignKey(ServiceClasses, on_delete=models.CASCADE, verbose_name='Вид мойки')
    negotiated_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Договорная цена', blank=True,
                                           null=True)
    employees = models.ForeignKey(Employees, on_delete=models.CASCADE, verbose_name='Автомойщик')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')
    is_completed = models.BooleanField(default=False, verbose_name='Выполнено')
    order_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата заказа')
    fund = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Фонд', blank=True, null=True)
    completion_date = models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')

    def save(self, *args, **kwargs):

        if not self.order_date:
            self.order_date = now()

        if not self.negotiated_price and self.type_of_car_wash:
            self.negotiated_price = self.type_of_car_wash.price

        if self.type_of_car_wash.name in ['Договорный', 'Комплексная мойка', 'Кузовная мойка',
                                          'Мойка двигателя', 'Мойка фур']:
            self.fund = 5000
        elif self.type_of_car_wash.name == 'Мойка грузовых':
            self.fund = 15000

        if self.car_photo:
            try:
                img = Image.open(self.car_photo)
                exif = img._getexif()
                if exif:
                    exif_dict = dict(exif.items())
                    orientation_key = next(
                        (key for key, value in ExifTags.TAGS.items() if value == 'Orientation'),
                        None
                    )
                    if orientation_key and orientation_key in exif_dict:
                        orientation = exif_dict[orientation_key]
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
            except Exception:
                pass
            max_dimensions = (1200, 1200)
            img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)
            output = BytesIO()
            img.save(output, format='WEBP', quality=70, optimize=True)
            output.seek(0)
            file_root = self.car_photo.name.rsplit('.', 1)[0]
            new_file_name = f"{file_root}.webp"
            self.car_photo.save(new_file_name, ContentFile(output.read()), save=False)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Заказ {self.id} - {self.employees}"

    class Meta:
        verbose_name = 'Заказ на мойку'
        verbose_name_plural = 'Заказы на мойку'
        ordering = ['-time_create']
