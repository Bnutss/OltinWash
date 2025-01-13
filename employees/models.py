from django.db import models
from datetime import date
from PIL import Image, ExifTags
import io
from django.core.files.uploadedfile import InMemoryUploadedFile


class Positions(models.Model):
    name_positions = models.CharField(max_length=100, verbose_name='Название должности', unique=True)
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    def __str__(self):
        return self.name_positions

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['-time_update', 'name_positions']


class Employees(models.Model):
    GENDER_CHOICES = [
        ('Мужской', 'Мужской'),
        ('Женский', 'Женский'),
    ]
    FIRED_CHOICES = [
        (True, 'Да'),
        (False, 'Нет'),
    ]
    name_employees = models.CharField(max_length=255, verbose_name='ФИО', unique=True)
    position = models.ForeignKey('Positions', on_delete=models.CASCADE, verbose_name='Должность')
    birth_date = models.DateField(null=True, blank=True, verbose_name='Дата рождения')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name='Пол')
    phone_number = models.CharField(max_length=20, verbose_name='Номер телефона')
    address = models.TextField(blank=True, verbose_name='Адрес проживания')
    hire_date = models.DateField(null=True, blank=True, verbose_name='Дата приёма на работу')
    passport_number = models.CharField(max_length=50, verbose_name='Серия и № паспорта')
    fired = models.BooleanField(default=False, verbose_name='Статус увольнения')
    date_of_termination = models.DateField(null=True, blank=True, verbose_name='Дата увольнения')
    default_photo_path = 'employees_photos/default.png'
    photo = models.ImageField(upload_to='employees_photos/', null=True, blank=True, verbose_name='Фото',
                              default=default_photo_path)
    time_update = models.DateTimeField(auto_now=True, verbose_name='Время изменения')
    time_create = models.DateTimeField(auto_now_add=True, verbose_name='Время создания')

    def fix_image_orientation(self, img):
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orientation = exif.get(orientation)
                if orientation == 3:
                    img = img.rotate(180, expand=True)
                elif orientation == 6:
                    img = img.rotate(270, expand=True)
                elif orientation == 8:
                    img = img.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            pass
        return img

    def save(self, *args, **kwargs):
        if not self.hire_date:
            self.hire_date = date.today()
        if self.fired and not self.date_of_termination:
            self.date_of_termination = date.today()

        if self.photo:
            img = Image.open(self.photo)
            img = self.fix_image_orientation(img)
            output = io.BytesIO()

            base_height = 300
            h_percent = (base_height / float(img.size[1]))
            w_size = int((float(img.size[0]) * h_percent))
            img = img.resize((w_size, base_height), Image.LANCZOS)
            img.save(output, format='WEBP', quality=85)
            output.seek(0)

            self.photo = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{self.photo.name.split('.')[0]}_processed.webp",
                'image/webp',
                output.tell(),
                None
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name_employees

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'
        ordering = ['-time_create', 'name_employees', 'fired']
