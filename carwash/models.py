from employees.models import Employees
from django.db import models
from django.contrib.auth.models import User
from django.utils.timezone import now
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    mobile_app = models.BooleanField(default=False, verbose_name='Мобильное приложение')
    delete_washorders = models.BooleanField(default=False, verbose_name='Может удалять заказы')
    delete_employees = models.BooleanField(default=False, verbose_name='Может удалять сотрудников')

    def __str__(self):
        return self.user.username


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
                                          'Комплексная мойка + мотор', 'Мойка фур']:
            self.fund = 10000
        elif self.type_of_car_wash.name == 'Мойка грузовых':
            self.fund = 20000

        # Конвертация изображения в WebP и изменение размера
        if self.car_photo:
            img = Image.open(self.car_photo)

            # Изменение размера изображения (максимальная ширина 1200 пикселей)
            max_width = 1200
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Конвертация в WebP
            output = BytesIO()
            img.save(output, format='WEBP', quality=85)
            output.seek(0)

            # Сохранение изображения
            self.car_photo.save(f"{self.car_photo.name.split('.')[0]}.webp", ContentFile(output.read()), save=False)

        super(WashOrders, self).save(*args, **kwargs)

    def __str__(self):
        return f"Заказ {self.id} - {self.employees}"

    class Meta:
        verbose_name = 'Заказ на мойку'
        verbose_name_plural = 'Заказы на мойку'
        ordering = ['-time_create']
