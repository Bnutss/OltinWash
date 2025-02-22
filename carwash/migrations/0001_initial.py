# Generated by Django 5.1.4 on 2025-01-13 07:22

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('employees', '0002_alter_employees_photo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Services',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_services', models.CharField(max_length=200, unique=True, verbose_name='Название услуги')),
                ('time_update', models.DateTimeField(auto_now=True, verbose_name='Время изменения')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
            ],
            options={
                'verbose_name': 'Услугу',
                'verbose_name_plural': 'Услуги',
                'ordering': ['-time_create', 'name_services'],
            },
        ),
        migrations.CreateModel(
            name='ServiceClasses',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=200, null=True, verbose_name='Название класса')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Цена класса')),
                ('time_update', models.DateTimeField(auto_now=True, verbose_name='Время изменения')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('services', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='carwash.services', verbose_name='Услуга')),
            ],
            options={
                'verbose_name': 'Класс услуг',
                'verbose_name_plural': 'Классы услуг',
                'ordering': ['-time_create', 'name'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mobile_app', models.BooleanField(default=False, verbose_name='Мобильное приложение')),
                ('delete_washorders', models.BooleanField(default=False, verbose_name='Может удалять заказы')),
                ('delete_employees', models.BooleanField(default=False, verbose_name='Может удалять сотрудников')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
        ),
        migrations.CreateModel(
            name='WashOrders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('car_photo', models.ImageField(upload_to='car_photos/', verbose_name='Фото авто')),
                ('negotiated_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Договорная цена')),
                ('time_create', models.DateTimeField(auto_now_add=True, verbose_name='Время создания')),
                ('is_completed', models.BooleanField(default=False, verbose_name='Выполнено')),
                ('order_date', models.DateTimeField(blank=True, null=True, verbose_name='Дата заказа')),
                ('fund', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Фонд')),
                ('completion_date', models.DateTimeField(blank=True, null=True, verbose_name='Дата завершения')),
                ('employees', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='employees.employees', verbose_name='Автомойщик')),
                ('type_of_car_wash', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='carwash.serviceclasses', verbose_name='Вид мойки')),
            ],
            options={
                'verbose_name': 'Заказ на мойку',
                'verbose_name_plural': 'Заказы на мойку',
                'ordering': ['-time_create'],
            },
        ),
    ]
