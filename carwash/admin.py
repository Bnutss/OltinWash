from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from carwash.models import ServiceClasses, WashOrders, Services, UserProfile, TelegramUser


# Инлайн-профиль пользователя
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False


# Кастомный админ для пользователя
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)


# Админ для услуг
@admin.register(Services)
class ServicesAdmin(admin.ModelAdmin):
    list_display = ('name_services',)
    list_display_links = ('name_services',)
    search_fields = ('name_services',)


# Админ для классов услуг
@admin.register(ServiceClasses)
class ServiceClassesAdmin(admin.ModelAdmin):
    list_display = ('name', 'services', 'price',)
    list_display_links = ('name',)
    search_fields = ('name',)
    list_filter = ('services',)
    autocomplete_fields = ('services',)


# Админ для заказов мойки
@admin.register(WashOrders)
class WashOrdersAdmin(admin.ModelAdmin):
    list_display = ('employees', 'type_of_car_wash', 'car_photo', 'is_completed', 'time_create')
    list_display_links = ('employees',)
    search_fields = ('employees__username',)  # Используем точный путь к полю
    list_filter = ('employees', 'type_of_car_wash')
    autocomplete_fields = ('employees', 'type_of_car_wash')


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'first_name', 'username', 'is_admin', 'created_at')
    list_filter = ('is_admin', 'created_at')
    search_fields = ('telegram_id', 'first_name', 'username')
    readonly_fields = ('created_at', 'updated_at')


# Заменяем стандартный UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
