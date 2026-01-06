from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Q
from django.contrib import messages
from .models import Service
from Accounts.models import User
from Bookings.models import Booking
from django.contrib.auth.decorators import login_required

@login_required
def service_list(request):
    services = Service.objects.select_related('provider').all()
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) |
            Q(provider__username__icontains=search_query) |
            Q(provider__first_name__icontains=search_query) |
            Q(provider__last_name__icontains=search_query)
        )
    
    if category_filter:
        services = services.filter(category=category_filter)
    
    # Get all categories from model choices
    all_category_choices = [choice[0] for choice in Service.CATEGORY_CHOICES]
    
    # Group services by category, then by provider
    categories_dict = {}
    for service in services:
        category = service.category
        provider = service.provider
        
        if category not in categories_dict:
            categories_dict[category] = {}
        
        if provider.id not in categories_dict[category]:
            categories_dict[category][provider.id] = {
                'provider': provider,
                'services': []
            }
        
        categories_dict[category][provider.id]['services'].append(service)
    
    # Create list for all categories 
    categories_list = []
    for category in all_category_choices:
        if category in categories_dict:
            providers_dict = categories_dict[category]
            providers_list = list(providers_dict.values())
            service_count = sum(len(p['services']) for p in providers_list)
        else:
            providers_list = []
            service_count = 0
        
        categories_list.append({
            'category': category,
            'providers': providers_list,
            'service_count': service_count
        })
    
    # Sort categories
    categories_list.sort(key=lambda x: x['category'])
    
    # Get all unique categories for filter dropdown
    all_categories = Service.objects.values_list('category', flat=True).distinct()
    
    context = {
        'categories_list': categories_list,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': all_categories,
    }
    return render(request, 'services.html', context)

@login_required
def service_providers(request):
    """List all service providers with their services and statistics"""
    providers = User.objects.filter(is_provider=True).annotate(
        service_count=Count('service'),
        total_bookings=Count('service__booking'),
        completed_bookings=Count('service__booking', filter=Q(service__booking__status='Completed')),
    )
    
    # Calculate earnings for each provider
    provider_list = []
    for provider in providers:
        completed_bookings = Booking.objects.filter(
            service__provider=provider,
            status='Completed'
        )
        total_earnings = sum(booking.service.price for booking in completed_bookings)
        
        provider_list.append({
            'provider': provider,
            'services': Service.objects.filter(provider=provider),
            'total_bookings': provider.total_bookings,
            'completed_bookings': provider.completed_bookings,
            'total_earnings': total_earnings,
        })
    
    # Search filter
    search_query = request.GET.get('search', '')
    if search_query:
        provider_list = [p for p in provider_list if 
                        search_query.lower() in p['provider'].username.lower() or
                        search_query.lower() in (p['provider'].first_name or '').lower() or
                        search_query.lower() in (p['provider'].last_name or '').lower()]
    
    context = {
        'provider_list': provider_list,
        'search_query': search_query,
    }
    return render(request, 'service_providers.html', context)
@login_required
def service_detail(request, service_id):
    """Display service details with provider information"""
    service = get_object_or_404(Service.objects.select_related('provider'), id=service_id)
    
    # Get provider statistics
    provider = service.provider
    provider_services = Service.objects.filter(provider=provider)
    total_bookings = Booking.objects.filter(service__provider=provider).count()
    completed_bookings = Booking.objects.filter(service__provider=provider, status='Completed').count()
    
    context = {
        'service': service,
        'provider': provider,
        'provider_services': provider_services,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
    }
    return render(request, 'service_detail.html', context)

@login_required
def toggle_service_availability(request, service_id):
    """Allow provider to toggle service availability"""
    if not request.user.is_provider:
        messages.error(request, 'You must be a service provider.')
        return redirect('services')
    
    service = get_object_or_404(Service, id=service_id)
    
    # Check if this service belongs to the logged-in provider
    if service.provider != request.user:
        messages.error(request, 'You do not have permission to modify this service.')
        return redirect('services')
    
    # Toggle availability
    service.is_available = not service.is_available
    service.save()
    
    status = "available" if service.is_available else "not available"
    messages.success(request, f'Service "{service.name}" is now {status}.')
    
    return redirect('provider_bookings')
