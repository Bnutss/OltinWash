from django.shortcuts import redirect
from django.views import View
from employees.models import Employees
from .models import WashOrders, ServiceClasses
from decimal import Decimal
import logging
from django.urls import reverse
import telegram
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import LoginSerializer, WashOrdersSerializer, ServiceClassesWithServiceNameSerializer, \
    WashOrdersListSerializer, EmployeeStatsSerializer, GeneralReportSerializer, EmployeeAtWorkSerializer, \
    EmployeeDetailWashOrderSerializer, WashOrderSerializer
from rest_framework import generics
import json
from rest_framework import status
from django.db.models import Count, Sum, Q, DecimalField
from django.db.models.functions import TruncDate

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from datetime import datetime, time
from django.utils.timezone import make_aware
from django.core.cache import cache
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


def check_orders(request):
    now = datetime.now()
    start_time = make_aware(datetime.combine(now.date(), time(9, 0)))
    end_time = make_aware(datetime.combine(now.date(), time(23, 0)))

    orders = WashOrders.objects.filter(time_create__range=(start_time, end_time))
    no_orders = orders.count() == 0

    return JsonResponse({'no_orders': no_orders})


class WashOrderDetailAPIView(APIView):
    def patch(self, request, pk):
        try:
            order = WashOrders.objects.get(pk=pk)
        except WashOrders.DoesNotExist:
            return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        if 'is_completed' in data:
            order.is_completed = data['is_completed']
            order.save()
            return Response(WashOrderSerializer(order).data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Некорректные данные'}, status=status.HTTP_400_BAD_REQUEST)


class EmployeeDetailWashOrdersListAPIView(generics.ListAPIView):
    serializer_class = EmployeeDetailWashOrderSerializer

    def get_queryset(self):
        employee_id = self.kwargs['employee_id']
        date_str = self.request.query_params.get('date', None)
        if date_str:
            selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = datetime.today().date()
        return WashOrders.objects.filter(employees__id=employee_id, order_date__date=selected_date)


class EmployeesAtWorkAPIView(APIView):
    def get(self, request, *args, **kwargs):
        date_str = request.GET.get('date')
        if date_str:
            try:
                selected_date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            selected_date = timezone.now().date()

        wash_orders_on_date = WashOrders.objects.filter(order_date__date=selected_date)
        employees_at_work = Employees.objects.filter(washorders__in=wash_orders_on_date).distinct()
        employees_with_incomplete_orders = [
            employee for employee in employees_at_work
            if wash_orders_on_date.filter(employees=employee, is_completed=False).exists()
        ]

        serializer = EmployeeAtWorkSerializer(employees_with_incomplete_orders, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class WashOrdersDeleteAPIView(generics.DestroyAPIView):
    queryset = WashOrders.objects.all()
    serializer_class = WashOrdersSerializer

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class SendTelegramMessageViewAPI(View):
    async def post(self, request, *args, **kwargs):
        bot_token = '6838645780:AAHX5ZTl3KQ_tyoy8XZaDfLnoFX182UJ2VQ'
        user_ids = ['1207702857', '121336069']
        total_amount = request.POST.get('total_amount')
        cashier_amount = request.POST.get('cashier_amount')
        employees_amount = request.POST.get('employees_amount')
        total_washes = request.POST.get('total_washes')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Функция форматирования чисел
        def format_number(value):
            value = float(value)
            if value.is_integer():
                return "{:,.0f}".format(value).replace(',', ' ')
            else:
                return "{:,.2f}".format(value).replace(',', ' ')

        total_amount = format_number(total_amount)
        cashier_amount = format_number(cashier_amount)
        employees_amount = format_number(employees_amount)

        message = (
            f"Отчет с {start_date} по {end_date}\n\n"
            f"Общее количество машин: {total_washes}\n\n"
            f"Итоговая сумма: {total_amount} UZS\n\n"
            f"Итоговая сумма для кассы: {cashier_amount} UZS\n\n"
            f"Итоговый заработок мойщиков: {employees_amount} UZS"
        )

        bot = telegram.Bot(token=bot_token)
        errors = []
        for user_id in user_ids:
            try:
                await bot.send_message(chat_id=user_id, text=message)
            except Exception as e:
                logging.error(f"Ошибка отправки в Telegram пользователю {user_id}: {e}")
                errors.append({'user_id': user_id, 'error': str(e)})

        if errors:
            return JsonResponse({'status': 'partial_success', 'errors': errors}, status=207)
        else:
            return JsonResponse({'status': 'success'}, status=200)


class GeneralReportAPIView(APIView):
    permission_classes = [AllowAny]  # Разрешаем доступ всем

    def get(self, request, format=None):
        """
        Возвращает общий отчет по заказам за указанный период.
        Параметры:
        - start_date: Начальная дата в формате 'YYYY-MM-DD'
        - end_date: Конечная дата в формате 'YYYY-MM-DD'
        """
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        # Валидация дат
        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты. Используйте формат YYYY-MM-DD.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Фильтрация заказов по дате
        wash_orders = WashOrders.objects.all()
        if start_date and end_date:
            wash_orders = wash_orders.filter(order_date__date__range=(start_date, end_date))

        # Проверка наличия заказов
        if not wash_orders.exists():
            return Response([], status=status.HTTP_200_OK)

        # Группировка и вычисление данных
        report_data = wash_orders.annotate(
            order_date_only=TruncDate('order_date')
        ).values('order_date_only').annotate(
            total_washes=Count('id'),
            total_amount=Sum('negotiated_price', output_field=DecimalField()),
            employees_amount=Sum('negotiated_price', output_field=DecimalField()) * Decimal('0.40'),
            cashier_amount=Sum('negotiated_price', output_field=DecimalField()) * Decimal('0.60')
        ).order_by('order_date_only')

        return Response(report_data, status=status.HTTP_200_OK)


class EmployeeStatsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        date = request.query_params.get('date', today)
        employees = Employees.objects.filter(washorders__isnull=False).distinct()
        stats = []

        for employee in employees:
            orders = WashOrders.objects.filter(employees=employee)
            if date:
                orders = orders.filter(order_date__date=date)
            washed_cars_count = orders.count()

            if washed_cars_count > 0:
                total_wash_amount = orders.aggregate(Sum('negotiated_price'))['negotiated_price__sum'] or 0.0
                total_wash_amount = float(total_wash_amount)
                employee_share = total_wash_amount * 0.4
                company_share = total_wash_amount * 0.6
                negotiated_washes_count = orders.filter(negotiated_price__isnull=False).count()
                fund_share = orders.aggregate(Sum('fund'))['fund__sum'] or 0.0

                stat = {
                    'id': employee.id,
                    'order_id': orders.first().id,  # Берем ID первого заказа
                    'name_employees': employee.name_employees,
                    'washed_cars_count': washed_cars_count,
                    'total_wash_amount': total_wash_amount,
                    'employee_share': employee_share,
                    'company_share': company_share,
                    'date': date,
                    'photo_url': employee.photo.url if employee.photo else '',
                    'negotiated_washes_count': negotiated_washes_count,
                    'fund_share': fund_share,
                    'is_completed': all(order.is_completed for order in orders),
                    'completion_date': orders.filter(is_completed=True).latest(
                        'order_date').completion_date if orders.filter(is_completed=True).exists() else None,
                }
                stats.append(stat)

        if not stats:
            return Response({"message": "No data available for the selected date"}, status=status.HTTP_200_OK)

        serializer = EmployeeStatsSerializer(stats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        employee_id = request.data.get('employee_id')
        if not employee_id:
            return Response({'error': 'Employee ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        today = timezone.now().date()
        orders = WashOrders.objects.filter(employees_id=employee_id, order_date__date=today)
        if not orders.exists():
            return Response({'error': 'No orders found for today for this employee'}, status=status.HTTP_404_NOT_FOUND)

        orders.update(is_completed=True, completion_date=timezone.now())
        return Response({'message': 'Orders updated successfully'}, status=status.HTTP_200_OK)


class WashOrdersListAPIView(APIView):
    def get(self, request):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        cache_key = f"wash_orders_{start_date}_{end_date}"
        wash_orders = cache.get(cache_key)

        if not wash_orders:
            filters = Q()
            if start_date and end_date:
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    filters &= Q(order_date__range=(start_date, end_date))
                except ValueError:
                    return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

            wash_orders = list(WashOrders.objects.filter(filters))
            cache.set(cache_key, wash_orders, timeout=300)  # Кэшировать на 5 минут

        serializer = WashOrdersListSerializer(wash_orders, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AddWashOrderAPIView(generics.CreateAPIView):
    permission_classes = [AllowAny]  # Разрешаем доступ всем
    serializer_class = WashOrdersSerializer

    def get_queryset(self):
        # Фильтруем мойщиков, исключая уволенных
        return Employees.objects.filter(fired=False)

    def perform_create(self, serializer):
        employee_id = self.request.data.get('employees')
        service_class_id = self.request.data.get('type_of_car_wash')
        negotiated_price = self.request.data.get('negotiated_price')

        if service_class_id:
            service_class = ServiceClasses.objects.get(id=service_class_id)

        if employee_id:
            employee = Employees.objects.get(id=employee_id)

        if negotiated_price:
            negotiated_price = Decimal(negotiated_price)
            serializer.save(employees=employee, type_of_car_wash=service_class, negotiated_price=negotiated_price)
        else:
            if service_class:
                negotiated_price = service_class.price
            serializer.save(employees=employee, type_of_car_wash=service_class, negotiated_price=negotiated_price)


class ServiceClassesListAPIView(generics.ListAPIView):
    queryset = ServiceClasses.objects.all()
    serializer_class = ServiceClassesWithServiceNameSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data = json.loads(json.dumps(response.data, ensure_ascii=False))
        return response


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            return Response({"message": "Успешный вход!", "user_id": user.id})
        return Response(serializer.errors, status=400)


class SendTelegramMessageView(View):
    async def post(self, request, *args, **kwargs):
        bot_token = '6838645780:AAHX5ZTl3KQ_tyoy8XZaDfLnoFX182UJ2VQ'
        chat_id = '-1002130067234'
        total_earnings = request.POST.get('total_earnings')
        message = request.POST.get('message')

        try:
            bot = telegram.Bot(token=bot_token)
            await bot.send_message(chat_id=chat_id, text=message)
            await bot.send_message(chat_id=chat_id, text=total_earnings)
        except Exception as e:
            logging.error(f"Ошибка отправки в Telegram: {e}")

        return redirect(reverse('carwash:main_menu'))
