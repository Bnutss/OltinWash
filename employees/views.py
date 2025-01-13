from django.shortcuts import get_object_or_404
from .models import Employees, Positions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import EmployeesSerializer, EmployeesDetailSerializer, EmployeeAddSerializer, PositionSerializer
from rest_framework import status
from rest_framework import generics
from django.db.models import ProtectedError


class WasherEmployeesListAPIView(generics.ListAPIView):
    serializer_class = EmployeesSerializer

    def get_queryset(self):
        # Получаем должность "Мойщик"
        washer_positions = Positions.objects.filter(name_positions='Мойщик')

        # Фильтруем сотрудников, которые являются мойщиками и не уволены
        return Employees.objects.filter(
            position__in=washer_positions,
            fired=False  # Исключаем уволенных
        ).order_by('name_employees')


class EmployeeDeleteAPIView(generics.DestroyAPIView):
    queryset = Employees.objects.all()
    serializer_class = EmployeesSerializer
    lookup_field = 'pk'

    def delete(self, request, *args, **kwargs):
        employee = self.get_object()
        if employee.washorders_set.exists():  # Проверяем наличие связанных заказов
            return Response({'error': 'Этот сотрудник привязан к активному заказу и не может быть удален.'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            self.perform_destroy(employee)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response({'error': 'Не удалось удалить сотрудника из-за связанных данных.'},
                            status=status.HTTP_400_BAD_REQUEST)


class EmployeesAPIListView(APIView):
    permission_classes = []

    def get(self, request):
        employees = Employees.objects.filter(fired=False)
        serializer = EmployeesSerializer(employees, many=True, context={'request': request})
        return Response(serializer.data)


class EmployeeDetailAPIView(APIView):
    def get(self, request, employee_id, format=None):
        try:
            employee = Employees.objects.get(id=employee_id)
        except Employees.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = EmployeesDetailSerializer(employee, context={'request': request})
        return Response(serializer.data)


class AddEmployeeAPIView(generics.CreateAPIView):
    queryset = Employees.objects.all()
    serializer_class = EmployeeAddSerializer


class FireEmployeeAPIView(APIView):
    def post(self, request, employee_id):
        employee = get_object_or_404(Employees, id=employee_id)
        employee.fired = True
        employee.save()
        return Response({'status': 'Сотрудник уволен'}, status=status.HTTP_200_OK)


class PositionsListAPIView(generics.ListAPIView):
    queryset = Positions.objects.all()
    serializer_class = PositionSerializer
