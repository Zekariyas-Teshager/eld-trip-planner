# backend/eld_app/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'trips', views.TripViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('plan-trip/', views.plan_trip, name='plan-trip'),
    path('download-pdf/<str:filename>/', views.download_pdf, name='download-pdf'),
    path('view-html-log/<str:filename>/', views.view_html_log, name='view-html-log'),  # ADD THIS
    path('day-logs/<int:day_number>/', views.get_day_logs, name='get-day-logs'),  # ADD THIS
    path('day-logs/<int:day_number>/<int:trip_id>/', views.get_day_logs, name='get-day-logs-with-trip'),  # ADD THIS
]