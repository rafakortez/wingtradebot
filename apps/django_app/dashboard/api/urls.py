"""API URLs for dashboard"""
from django.urls import path
from . import views

# URLs without trailing slashes to match Flask pattern
# Django will handle both with and without trailing slashes
urlpatterns = [
    path('status/<str:login_number>', views.get_status, name='api-status'),
    path('status/<str:login_number>/', views.get_status, name='api-status-slash'),
    path('recent-db-orders/<str:login_number>', views.get_recent_db_orders, name='api-recent-db-orders'),
    path('recent-db-orders/<str:login_number>/', views.get_recent_db_orders, name='api-recent-db-orders-slash'),
    path('webhook-outcomes/<str:login_number>', views.get_webhook_outcomes, name='api-webhook-outcomes'),
    path('webhook-outcomes/<str:login_number>/', views.get_webhook_outcomes, name='api-webhook-outcomes-slash'),
    path('recent-logs', views.get_recent_logs, name='api-recent-logs'),
    path('recent-logs/', views.get_recent_logs, name='api-recent-logs-slash'),
    path('simplefx-chart-data', views.get_chart_data, name='api-chart-data'),
    path('simplefx-chart-data/', views.get_chart_data, name='api-chart-data-slash'),
]


