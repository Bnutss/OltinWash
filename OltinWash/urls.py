from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from test_webhook import test_webhook
from webhook_view import telegram_webhook

urlpatterns = [
    path('admin/', admin.site.urls),
    path('employees/', include('employees.urls', namespace='employees')),
    path('', include('carwash.urls', namespace='carwash')),
    path('webhook/telegram/', telegram_webhook, name='telegram_webhook'),
    path('test/', test_webhook, name='test_webhook'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
