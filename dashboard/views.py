from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count
from Accounts.models import User
from Services.models import Service
from Bookings.models import Booking

from django.contrib.auth.decorators import login_required, user_passes_test

def superuser_required(user):
    return user.is_superuser

@login_required
@user_passes_test(superuser_required)
def dashboard_home(request):
    total_users = User.objects.count()
    total_customers = User.objects.filter(is_customer=True).count()
    total_providers = User.objects.filter(is_provider=True).count()
    total_services = Service.objects.count()
    total_bookings = Booking.objects.count()
    pending_bookings = Booking.objects.filter(status='Pending').count()
    accepted_bookings = Booking.objects.filter(status='Accepted').count()
    completed_bookings = Booking.objects.filter(status='Completed').count()
    
    # Recent bookings
    recent_bookings = Booking.objects.select_related('customer', 'service').order_by('-id')[:5]
    
    # Bookings by status
    bookings_by_status = Booking.objects.values('status').annotate(count=Count('id'))
    
    # Services by category
    services_by_category = Service.objects.values('category').annotate(count=Count('id'))

    context = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_providers': total_providers,
        'total_services': total_services,
        'total_bookings': total_bookings,
        'pending_bookings': pending_bookings,
        'accepted_bookings': accepted_bookings,
        'completed_bookings': completed_bookings,
        'recent_bookings': recent_bookings,
        'bookings_by_status': bookings_by_status,
        'services_by_category': services_by_category,
    }
    return render(request, 'dashboard/home/index.html', context)

@login_required
@user_passes_test(superuser_required)
def users_list(request):
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    if role_filter == 'customer':
        users = users.filter(is_customer=True)
    elif role_filter == 'provider':
        users = users.filter(is_provider=True)
    
    users = users.order_by('-id')
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'dashboard/users/index.html', context)

@login_required
@user_passes_test(superuser_required)
def services_list(request):
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    services = Service.objects.select_related('provider').all()
    
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) |
            Q(provider__username__icontains=search_query)
        )
    
    if category_filter:
        services = services.filter(category=category_filter)
    
    services = services.order_by('-id')
    
    # Get unique categories for filter
    categories = Service.objects.values_list('category', flat=True).distinct()
    
    context = {
        'services': services,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': categories,
    }
    return render(request, 'dashboard/services/index.html', context)

@login_required
@user_passes_test(superuser_required)
def bookings_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    
    bookings = Booking.objects.select_related('customer', 'service').all()
    
    if search_query:
        bookings = bookings.filter(
            Q(customer__username__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )
    
    if status_filter:
        bookings = bookings.filter(status=status_filter)
    
    bookings = bookings.order_by('-id')
    
    context = {
        'bookings': bookings,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'dashboard/bookings/index.html', context)

@login_required
@user_passes_test(superuser_required)
def update_booking_status(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        new_status = request.POST.get('status')
        if new_status in dict(Booking.STATUS_CHOICES):
            booking.status = new_status
            booking.save()
            messages.success(request, f'Booking #{booking.id} status updated to {new_status}.')
        else:
            messages.error(request, 'Invalid status selected.')
    return redirect('dashboard_bookings')

@login_required
@user_passes_test(superuser_required)
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        if user.is_superuser:
            messages.error(request, 'Cannot delete superuser account.')
        else:
            username = user.username
            user.delete()
            messages.success(request, f'User {username} has been deleted.')
    return redirect('dashboard_users')

@login_required
@user_passes_test(superuser_required)
def delete_service(request, service_id):
    if request.method == 'POST':
        service = get_object_or_404(Service, id=service_id)
        service_name = service.name
        service.delete()
        messages.success(request, f'Service {service_name} has been deleted.')
    return redirect('dashboard_services')

@login_required
@user_passes_test(superuser_required)
def delete_booking(request, booking_id):
    if request.method == 'POST':
        booking = get_object_or_404(Booking, id=booking_id)
        booking.delete()
        messages.success(request, f'Booking #{booking_id} has been deleted.')
    return redirect('dashboard_bookings')

@login_required
@user_passes_test(superuser_required)
def view_customers(request):
    search_query = request.GET.get('search', '')
    
    customers = User.objects.filter(is_customer=True)
    
    if search_query:
        customers = customers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    customers = customers.order_by('-id')
    
    context = {
        'customers': customers,
        'search_query': search_query,
    }
    return render(request, 'dashboard/users/customers.html', context)

@login_required
@user_passes_test(superuser_required)
def view_providers(request):
    search_query = request.GET.get('search', '')
    
    providers = User.objects.filter(is_provider=True)
    
    if search_query:
        providers = providers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query)
        )
    
    providers = providers.order_by('-id')
    
    context = {
        'providers': providers,
        'search_query': search_query,
    }
    return render(request, 'dashboard/users/providers.html', context)

@login_required
@user_passes_test(superuser_required)
def pending_bookings(request):
    search_query = request.GET.get('search', '')
    
    bookings = Booking.objects.select_related('customer', 'service').filter(status='Pending')
    
    if search_query:
        bookings = bookings.filter(
            Q(customer__username__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )
    
    bookings = bookings.order_by('-id')
    
    context = {
        'bookings': bookings,
        'search_query': search_query,
        'status_choices': Booking.STATUS_CHOICES,
    }
    return render(request, 'dashboard/bookings/pending.html', context)
