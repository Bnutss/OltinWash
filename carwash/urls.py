from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import SendTelegramMessageView, LoginAPIView, AddWashOrderAPIView, ServiceClassesListAPIView, \
    WashOrdersListAPIView, EmployeeStatsAPIView, GeneralReportAPIView, SendTelegramMessageViewAPI, \
    EmployeesAtWorkAPIView, EmployeeDetailWashOrdersListAPIView, WashOrdersDeleteAPIView, \
    WashOrderDetailAPIView, check_orders

app_name = 'carwash'

urlpatterns = [
    path('api/login/', LoginAPIView.as_view(), name='api_login'),
    path('send_telegram_message/', SendTelegramMessageView.as_view(), name='send_telegram_message'),
    path('api/add_order/', AddWashOrderAPIView.as_view(), name='add_order_api'),
    path('api/service_classes/', ServiceClassesListAPIView.as_view(), name='service_classes'),
    path('api/wash-orders/', WashOrdersListAPIView.as_view(), name='wash-orders-list'),
    path('api/employee-stats/', EmployeeStatsAPIView.as_view(), name='employee-stats'),
    path('api/report/', GeneralReportAPIView.as_view(), name='general_report'),
    path('api/send_telegram_message/', SendTelegramMessageViewAPI.as_view(), name='send_telegram_message'),
    path('api/wash-orders/<int:pk>/', WashOrdersDeleteAPIView.as_view(), name='washorder-delete'),
    path('api/employees/at-work/', EmployeesAtWorkAPIView.as_view(), name='employees-at-work'),
    path('api/employee/<int:employee_id>/wash_orders/', EmployeeDetailWashOrdersListAPIView.as_view(),
         name='employee-wash-orders-list'),
    path('api/wash-orders/<int:pk>/', WashOrdersDeleteAPIView.as_view(), name='wash-orders-delete'),
    path('api/orders/<int:pk>/', WashOrderDetailAPIView.as_view(), name='order-detail'),
    path('api/check_orders/', check_orders, name='check_orders'),
]
