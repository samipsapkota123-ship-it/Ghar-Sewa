from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_home, name='dashboard_home'),
    path('users/', views.users_list, name='dashboard_users'),
    path('users/<int:user_id>/delete/', views.delete_user, name='dashboard_delete_user'),
    path('users/customers/', views.view_customers, name='dashboard_view_customers'),
    path('users/providers/', views.view_providers, name='dashboard_view_providers'),
    path('services/', views.services_list, name='dashboard_services'),
    path('services/<int:service_id>/delete/', views.delete_service, name='dashboard_delete_service'),
    path('bookings/', views.bookings_list, name='dashboard_bookings'),
    path('bookings/pending/', views.pending_bookings, name='dashboard_pending_bookings'),
    path('bookings/<int:booking_id>/update-status/', views.update_booking_status, name='dashboard_update_booking_status'),
    path('bookings/<int:booking_id>/delete/', views.delete_booking, name='dashboard_delete_booking'),
]
