from django.urls import path
from .views import service_list, service_providers, service_detail, toggle_service_availability

urlpatterns = [
    path('', service_list, name='services'),
    path('providers/', service_providers, name='service_providers'),
    path('<int:service_id>/', service_detail, name='service_detail'),
    path('<int:service_id>/toggle-availability/', toggle_service_availability, name='toggle_service_availability'),
]
