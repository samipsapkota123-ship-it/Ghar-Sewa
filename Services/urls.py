from django.urls import path
from .views import (
    service_list, service_providers, service_detail, toggle_service_availability,
    plumbing_services, electrical_services, cleaning_services, painting_services,
    appliance_repair_services, handyman_services,
    plumbing_providers, electrical_providers, cleaning_providers, painting_providers,
    appliance_repair_providers, handyman_providers
)

urlpatterns = [
    path('', service_list, name='services'),
    path('providers/', service_providers, name='service_providers'),
    path('<int:service_id>/', service_detail, name='service_detail'),
    path('<int:service_id>/toggle-availability/', toggle_service_availability, name='toggle_service_availability'),

    # Service category pages
    path('plumbing/', plumbing_services, name='plumbing'),
    path('electrical/', electrical_services, name='electrical'),
    path('cleaning/', cleaning_services, name='cleaning'),
    path('painting/', painting_services, name='painting'),
    path('appliance-repair/', appliance_repair_services, name='appliance_repair'),
    path('handyman/', handyman_services, name='handyman'),

    # Service provider pages
    path('plumbing/providers/', plumbing_providers, name='plumbing_providers'),
    path('electrical/providers/', electrical_providers, name='electrical_providers'),
    path('cleaning/providers/', cleaning_providers, name='cleaning_providers'),
    path('painting/providers/', painting_providers, name='painting_providers'),
    path('appliance-repair/providers/', appliance_repair_providers, name='appliance_repair_providers'),
    path('handyman/providers/', handyman_providers, name='handyman_providers'),
]
