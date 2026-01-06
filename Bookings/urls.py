from django.urls import path
from .views import (
    book_service,
    my_bookings,
    provider_bookings,
    update_booking_status_provider,
    mark_payment_received,
    make_payment,
    EsewaBookingView,
    esewa_verify_booking,
    payment_failed,
   
)

urlpatterns = [
    path('book/<int:service_id>/', book_service, name='book_service'),
    path('my-bookings/', my_bookings, name='my_bookings'),
    path('provider-bookings/', provider_bookings, name='provider_bookings'),
    path(
        'provider-bookings/<int:booking_id>/update-status/',
        update_booking_status_provider,
        name='update_booking_status_provider',
    ),
    path(
        'provider-bookings/<int:booking_id>/mark-payment-received/',
        mark_payment_received,
        name='mark_payment_received',
    ),
    path(
        'my-bookings/<int:booking_id>/make-payment/',
        make_payment,
        name='make_payment',
    ),
    # Esewa payment for a booking
    path( 'my-bookings/<int:booking_id>/esewa/', EsewaBookingView.as_view(), name='booking_esewa', ),
    path(
    'my-bookings/<int:booking_id>/esewa-verify/',
    esewa_verify_booking,
    name='esewa_verify_booking',
),
    
    path("payment-failed/", payment_failed, name="payment_failed")

]
