"""URLs for dashboard app"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('resumo/', views.resumo_view, name='resumo'),
    path('charts/', views.charts_view, name='charts'),
]



