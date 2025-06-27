from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def test_webhook(request):
    return HttpResponse("Test webhook works!")
