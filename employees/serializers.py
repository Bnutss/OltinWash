from datetime import date
from rest_framework import serializers
from .models import Employees, Positions


class EmployeesSerializer(serializers.ModelSerializer):
    position_name = serializers.CharField(source='position.name_positions', read_only=True)
    photo_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Employees
        fields = ['id', 'name_employees', 'position_name', 'photo_url', 'age']

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url'):
            return request.build_absolute_uri(obj.photo.url)
        return None

    def get_age(self, obj):
        if obj.birth_date:
            today = date.today()
            age = today.year - obj.birth_date.year - (
                        (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
            return age
        return None


class EmployeesDetailSerializer(serializers.ModelSerializer):
    position_name = serializers.CharField(source='position.name_positions', read_only=True)
    photo_url = serializers.SerializerMethodField()
    age = serializers.SerializerMethodField()

    class Meta:
        model = Employees
        fields = [
            'id',
            'name_employees',
            'position_name',
            'birth_date',
            'age',
            'gender',
            'phone_number',
            'address',
            'hire_date',
            'passport_number',
            'fired',
            'date_of_termination',
            'photo_url',
            'time_update',
            'time_create'
        ]
        read_only_fields = ['id', 'time_update', 'time_create']

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if obj.photo and hasattr(obj.photo, 'url'):
            return request.build_absolute_uri(obj.photo.url)
        return None

    def get_age(self, obj):
        if obj.birth_date:
            today = date.today()
            age = today.year - obj.birth_date.year - (
                        (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day))
            return age
        return None


class EmployeeAddSerializer(serializers.ModelSerializer):
    birth_date = serializers.DateField(input_formats=['%d.%m.%Y'])

    class Meta:
        model = Employees
        fields = '__all__'


class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Positions
        fields = ['id', 'name_positions']
