from django.contrib import admin
from employees.models import Employees, Positions


@admin.register(Employees)
class EmployeesAdmin(admin.ModelAdmin):
    list_display = (
        'name_employees', 'birth_date', 'position', 'fired', 'passport_number', 'date_of_termination'
    )
    list_display_links = ('name_employees',)
    search_fields = ('name_employees', 'passport_number', 'phone_number')
    autocomplete_fields = ['position']
    list_filter = ('position', 'fired', 'hire_date', 'date_of_termination')
    ordering = ('-time_create', 'name_employees')
    date_hierarchy = 'hire_date'
    fieldsets = (
        (None, {
            'fields': ('name_employees', 'position', 'birth_date', 'gender', 'phone_number', 'address', 'photo')
        }),
        ('Рабочие данные', {
            'fields': ('hire_date', 'fired', 'date_of_termination', 'passport_number'),
            'classes': ('collapse',),
        }),
        ('Техническая информация', {
            'fields': ('time_create', 'time_update'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('time_create', 'time_update')


@admin.register(Positions)
class PositionsAdmin(admin.ModelAdmin):
    list_display = ('name_positions',)
    list_display_links = ('name_positions',)
    search_fields = ('name_positions',)
    ordering = ('name_positions',)
