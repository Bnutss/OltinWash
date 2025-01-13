from rest_framework import serializers
from .models import WashOrders, ServiceClasses
from django.contrib.auth import authenticate
from employees.serializers import EmployeesSerializer
from employees.models import Employees, Positions
from decimal import Decimal


class EmployeeDetailWashOrderSerializer(serializers.ModelSerializer):
    employee_share = serializers.SerializerMethodField()
    company_share = serializers.SerializerMethodField()
    car_photo_url = serializers.SerializerMethodField()

    class Meta:
        model = WashOrders
        fields = [
            'id',
            'type_of_car_wash',
            'negotiated_price',
            'order_date',
            'is_completed',
            'fund',
            'employee_share',
            'company_share',
            'car_photo_url',
        ]
        depth = 1

    def get_employee_share(self, obj):
        if obj.negotiated_price:
            return obj.negotiated_price * Decimal('0.4')
        return Decimal('0.0')

    def get_company_share(self, obj):
        if obj.negotiated_price:
            return obj.negotiated_price * Decimal('0.6')
        return Decimal('0.0')

    def get_car_photo_url(self, obj):
        request = self.context.get('request')
        if obj.car_photo and request:
            return request.build_absolute_uri(obj.car_photo.url)
        return None


class EmployeeAtWorkSerializer(serializers.ModelSerializer):
    position_name = serializers.CharField(source='position.name_positions', read_only=True)
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Employees
        fields = ['id', 'name_employees', 'position_name', 'photo_url']

    def get_photo_url(self, obj):
        request = self.context.get('request')
        if request is None:
            return None
        photo_url = obj.photo.url if obj.photo else None
        return request.build_absolute_uri(photo_url) if photo_url else None


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user and user.is_active:
            if hasattr(user, 'userprofile') and user.userprofile.mobile_app:
                return user
            else:
                raise serializers.ValidationError("Этот пользователь не имеет доступа через мобильное приложение.")
        raise serializers.ValidationError("Неправильный логин или пароль.")


class WashOrdersSerializer(serializers.ModelSerializer):
    class Meta:
        model = WashOrders
        fields = '__all__'


class WashOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = WashOrders
        fields = '__all__'


class ServiceClassesWithServiceNameSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='services.name_services', read_only=True)

    class Meta:
        model = ServiceClasses
        fields = ['id', 'name', 'price', 'time_update', 'time_create', 'services', 'service_name']


class WashOrdersListSerializer(serializers.ModelSerializer):
    employees = EmployeesSerializer(required=False, allow_null=True)
    type_of_car_wash = ServiceClassesWithServiceNameSerializer(required=False, allow_null=True)
    price_to_display = serializers.SerializerMethodField()

    class Meta:
        model = WashOrders
        fields = ['id', 'car_photo', 'negotiated_price', 'order_date', 'is_completed', 'employees', 'type_of_car_wash',
                  'price_to_display']

    def get_price_to_display(self, obj):
        car_wash_name = obj.type_of_car_wash.name.strip().lower()
        if car_wash_name == "договор":
            return obj.negotiated_price
        elif obj.type_of_car_wash.price is not None:
            return obj.type_of_car_wash.price
        return None


class EmployeeStatsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    name_employees = serializers.CharField(max_length=200)
    washed_cars_count = serializers.IntegerField()
    total_wash_amount = serializers.FloatField()
    employee_share = serializers.FloatField()
    company_share = serializers.FloatField()
    date = serializers.DateTimeField()
    photo_url = serializers.URLField(allow_blank=True)
    negotiated_washes_count = serializers.IntegerField()
    fund_share = serializers.FloatField()
    is_completed = serializers.BooleanField()
    completion_date = serializers.DateTimeField(allow_null=True)


class GeneralReportSerializer(serializers.Serializer):
    total_washes = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    cashier_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    employees_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
