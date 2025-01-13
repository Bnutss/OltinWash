from django.urls import path
from employees.views import (
    EmployeesAPIListView, EmployeeDetailAPIView, FireEmployeeAPIView, PositionsListAPIView, EmployeeDeleteAPIView,
    WasherEmployeesListAPIView, AddEmployeeAPIView
)

app_name = 'employees'

urlpatterns = [
    path('api/employees/', EmployeesAPIListView.as_view(), name='employees_api_list'),
    path('api/employee/<int:employee_id>/', EmployeeDetailAPIView.as_view(), name='employee_detail_api'),
    path('api/employees/<int:employee_id>/fire/', FireEmployeeAPIView.as_view(), name='fire_employee_api'),
    path('api/positions/', PositionsListAPIView.as_view(), name='positions_list_api'),
    path('api/employees/add/', AddEmployeeAPIView.as_view(), name='add_employee_api'),
    path('api/employees/<int:pk>/delete/', EmployeeDeleteAPIView.as_view(), name='employee-delete'),
    path('api/washer_employees/', WasherEmployeesListAPIView.as_view(), name='washer-employees-list'),

]
