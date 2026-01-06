from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views import View
from django.http import HttpResponseBadRequest
from django.urls import reverse
from .models import Booking
from Services.models import Service
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Sum
import uuid
import json
import base64
from .esewa_signature import genSha256

@login_required
def book_service(request, service_id):
    service = get_object_or_404(Service.objects.select_related('provider'), id=service_id)

    if request.method == 'POST':
        date = request.POST.get('date')
        time = request.POST.get('time')
        address = request.POST.get('address', '').strip()
        phone_number = request.POST.get('phone_number', '').strip()
        payment_method = request.POST.get('payment_method', 'Cash')

        if not date or not time:
            messages.error(request, 'Please provide both date and time.')
            return render(request, 'book_service.html', {'service': service})
        
        if not address:
            messages.error(request, 'Please provide a service address.')
            return render(request, 'book_service.html', {'service': service})
        
        if not phone_number:
            messages.error(request, 'Please provide your phone number.')
            return render(request, 'book_service.html', {'service': service})

        Booking.objects.create(
            customer=request.user,
            service=service,
            date=date,
            time=time,
            address=address,
            phone_number=phone_number,
            payment_method=payment_method,
            payment_status='Pending'
        )
        messages.success(request, f'Booking created for {service.name}!')
        return redirect('my_bookings')

    return render(request, 'book_service.html', {'service': service})

@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(customer=request.user).select_related('service', 'service__provider').order_by('-date', '-time')
    return render(request, 'my_bookings.html', {'bookings': bookings})

@login_required
def provider_bookings(request):
    """View bookings for services provided by the logged-in provider"""
    if not request.user.is_provider:
        messages.error(request, 'You must be a service provider to access this page.')
        return redirect('home')
    
    # Get all services owned by this provider
    my_services = Service.objects.filter(provider=request.user)
    
    # Get all bookings for these services
    bookings = Booking.objects.filter(service__in=my_services).select_related('customer', 'service').order_by('-date', '-time')
    
    # Statistics
    total_bookings = bookings.count()
    pending_bookings = bookings.filter(status='Pending').count()
    accepted_bookings = bookings.filter(status='Accepted').count()
    completed_bookings = bookings.filter(status='Completed').count()
    # Only count earnings from completed bookings where payment is received
    total_earnings = bookings.filter(status='Completed', payment_received=True).aggregate(total=Sum('service__price'))['total'] or 0
    paid_bookings = bookings.filter(payment_received=True).count()
    unpaid_bookings = bookings.filter(status='Completed', payment_received=False).count()
    
    # Filter by status if requested
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    context = {
        'bookings': bookings,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'accepted_bookings': accepted_bookings,
        'completed_bookings': completed_bookings,
        'total_earnings': total_earnings,
        'paid_bookings': paid_bookings,
        'unpaid_bookings': unpaid_bookings,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'provider_bookings.html', context)

@login_required
def update_booking_status_provider(request, booking_id):
    """Allow provider to update booking status"""
    if not request.user.is_provider:
        messages.error(request, 'You must be a service provider.')
        return redirect('home')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if this booking is for a service owned by this provider
    if booking.service.provider != request.user:
        messages.error(request, 'You do not have permission to update this booking.')
        return redirect('provider_bookings')

    # If booking already marked Not Available, block further status updates
    if booking.status == 'Not Available':
        messages.error(request, 'Status updates are disabled for bookings marked as Not Available.')
        return redirect('provider_bookings')
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        # Allow providers to set any valid status except when already Not Available
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            if new_status == 'Not Available':
                booking.payment_status = 'Cancelled'
                booking.payment_received = False
            booking.save()
            messages.success(request, f'Booking #{booking.id} status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status selected.')
    
    return redirect('provider_bookings')

@login_required
def mark_payment_received(request, booking_id):
    """Allow provider to mark payment as received"""
    if not request.user.is_provider:
        messages.error(request, 'You must be a service provider.')
        return redirect('home')
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if this booking is for a service owned by this provider
    if booking.service.provider != request.user:
        messages.error(request, 'You do not have permission to update this booking.')
        return redirect('provider_bookings')
    
    if request.method == 'POST':
        if booking.payment_status != 'Paid':
            messages.error(request, 'Customer must mark payment as Paid before you can mark it as received.')
            return redirect('provider_bookings')

        booking.payment_received = True
        booking.payment_status = 'Received'
        booking.save()
        messages.success(request, f'Payment for Booking #{booking.id} marked as received.')
    
    return redirect('provider_bookings')


@login_required
def make_payment(request, booking_id):
    """Handle customer payment for a booking.

    - For Cash / Khalti: customer confirms and we mark as Paid.
    - For Esewa: redirect to Esewa payment form first.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Check if this booking belongs to the logged-in customer
    if booking.customer != request.user:
        messages.error(request, 'You do not have permission to access this booking.')
        return redirect('my_bookings')
    
    if request.method == 'POST':
        # If Esewa is selected, send user to Esewa payment page
        if booking.payment_method == 'Esewa':
            return redirect('booking_esewa', booking_id=booking.id)

        # For other methods (Cash, Khalti, etc.), mark as paid directly
        booking.payment_status = 'Paid'
        booking.save()
        messages.success(
            request,
            f'Payment for Booking #{booking.id} has been marked as paid. The provider will confirm receipt.'
        )
        return redirect('my_bookings')
    
    # GET request - show payment confirmation page
    return render(request, 'make_payment.html', {'booking': booking})


class EsewaBookingView(View):
    """Start Esewa payment for a booking."""

    def get(self, request, booking_id, *args, **kwargs):
        booking = get_object_or_404(Booking, id=booking_id)

        # Security: only the customer who owns this booking can pay for it
        if booking.customer != request.user:
            messages.error(request, 'You do not have permission to access this booking.')
            return redirect('my_bookings')

        amount = booking.service.price
        total_amount = amount  # no extra charges

        transaction_uuid = uuid.uuid4()

        secret_key = '8gBm/:&EnhH.1/q'
        data_to_sign = (
            f"total_amount={total_amount},"
            f"transaction_uuid={transaction_uuid},"
            f"product_code=EPAYTEST"
        )
        result = genSha256(secret_key, data_to_sign)

        success_url = request.build_absolute_uri(
            reverse('esewa_verify_booking', args=[booking.id])
        )
        failure_url = request.build_absolute_uri(
            reverse('payment_failed')
        )

        data = {
            'amount': amount,
            'total_amount': total_amount,
            'transaction_uuid': transaction_uuid,
            'product_code': 'EPAYTEST',
            'signature': result,
            'success_url': success_url,
            'failure_url': failure_url,
        }

        return render(
            request,
            'bookings/esewaform.html',
            {
                'booking': booking,
                'data': data,
            },
        )


def esewa_verify_booking(request, booking_id):
    """Handle Esewa callback and update booking payment status."""
    data = request.GET.get('data')
    if not data:
        return HttpResponseBadRequest('Missing payment data.')

    try:
        decoded_data = base64.b64decode(data).decode('utf-8')
        map_data = json.loads(decoded_data)
    except Exception:
        return HttpResponseBadRequest('Invalid payment data.')

    booking = get_object_or_404(Booking, id=booking_id)

    status = str(map_data.get('status', '')).lower()

    if status == 'complete':
        booking.payment_status = 'Paid'
        booking.save()
        messages.success(
            request,
            f'Esewa payment for Booking #{booking.id} was successful. The provider will confirm receipt.',
        )
    else:
        booking.payment_status = 'Failed'
        booking.save()
        messages.error(
            request,
            f'Esewa payment for Booking #{booking.id} failed or was cancelled.',
        )

    return redirect('my_bookings')


def payment_failed(request):
    return render(request, "bookings/payment_failed.html")
