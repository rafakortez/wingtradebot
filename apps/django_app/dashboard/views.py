"""Views for dashboard app"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import requests
from shared.config import Config


def dashboard_view(request):
    """Main dashboard view"""
    return render(request, 'dashboard/index.html')


def resumo_view(request):
    """Resumo view"""
    return render(request, 'dashboard/index.html')


def charts_view(request):
    """Charts view"""
    return render(request, 'dashboard/index.html')


@csrf_exempt
def webhook_view(request):
    """Process TradingView webhook"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # This would process webhook and call FastAPI service
    # Implementation similar to Flask version
    return JsonResponse({'status': 'received'})


