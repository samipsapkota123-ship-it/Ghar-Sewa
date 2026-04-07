from collections import defaultdict

from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Count, Avg, Q
from django.contrib import messages

from .models import Service
from .algorithm_utils import (
    add_ratings_to_category_list,
    add_ratings_to_provider_items,
    filter_providers_by_search,
    match_exact_username,
    provider_matches_search,
)
from Accounts.models import User
from Bookings.models import Booking, ReviewRating
from django.contrib.auth.decorators import login_required


def group_provider_items_by_company(provider_list):
    """Group [{'provider': User, ...}, ...] by provider.company_name (sorted A–Z)."""
    by_company = defaultdict(list)
    for item in provider_list:
        cn = (item['provider'].company_name or '').strip() or '—'
        by_company[cn].append(item)
    return [
        {
            'company_name': name,
            'providers': sorted(items, key=lambda x: x['provider'].username.lower()),
        }
        for name, items in sorted(by_company.items(), key=lambda x: x[0].lower())
    ]

@login_required
def service_list(request):
    # Only list services from providers registered under a company (bookable providers)
    services = Service.objects.select_related('provider').exclude(provider__company_name='')
    
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    
    if search_query:
        services = services.filter(
            Q(name__icontains=search_query) |
            Q(provider__username__icontains=search_query) |
            Q(provider__first_name__icontains=search_query) |
            Q(provider__last_name__icontains=search_query) |
            Q(provider__company_name__icontains=search_query)
        )
    
    if category_filter:
        services = services.filter(category=category_filter)
    
    # Get all categories from model choices
    all_category_choices = [choice[0] for choice in Service.CATEGORY_CHOICES]
    
    # Group: category → company → provider → services
    categories_dict = {}
    for service in services:
        category = service.category
        provider = service.provider
        company = (provider.company_name or '').strip() or '—'

        if category not in categories_dict:
            categories_dict[category] = {}
        if company not in categories_dict[category]:
            categories_dict[category][company] = {}
        if provider.id not in categories_dict[category][company]:
            categories_dict[category][company][provider.id] = {
                'provider': provider,
                'services': [],
            }
        categories_dict[category][company][provider.id]['services'].append(service)

    # Create list for all categories
    categories_list = []
    for category in all_category_choices:
        if category in categories_dict:
            companies_dict = categories_dict[category]
            companies_list = []
            for company_name in sorted(companies_dict.keys(), key=lambda x: x.lower()):
                prov_map = companies_dict[company_name]
                providers_list = list(prov_map.values())
                companies_list.append({
                    'company_name': company_name,
                    'providers': providers_list,
                })
            service_count = sum(
                len(p['services'])
                for co in companies_list
                for p in co['providers']
            )
        else:
            companies_list = []
            service_count = 0

        categories_list.append({
            'category': category,
            'companies': companies_list,
            'service_count': service_count,
        })

    # Sort categories
    categories_list.sort(key=lambda x: x['category'])

    add_ratings_to_category_list(categories_list)
    
    # Get all unique categories for filter dropdown
    all_categories = Service.objects.exclude(provider__company_name='').values_list('category', flat=True).distinct()
    
    context = {
        'categories_list': categories_list,
        'search_query': search_query,
        'category_filter': category_filter,
        'categories': all_categories,
    }
    return render(request, 'services.html', context)

@login_required
def service_providers(request):
    """Category → company → providers (customer marketplace view)."""
    raw_search = request.GET.get('search', '').strip()
    search_lower = raw_search.lower()

    all_categories = [c[0] for c in Service.CATEGORY_CHOICES]
    category_sections = []

    for idx, category in enumerate(all_categories):
        provider_ids = (
            Service.objects.filter(provider__is_provider=True)
            .exclude(provider__company_name='')
            .filter(category=category)
            .values_list('provider_id', flat=True)
            .distinct()
        )
        providers = User.objects.filter(id__in=provider_ids).exclude(company_name='').order_by(
            'username'
        )
        plist = list(providers)
        used_exact = False
        if raw_search:
            plist, used_exact = match_exact_username(plist, search_lower)

        provider_list = []
        for provider in plist:
            services = Service.objects.filter(provider=provider, category=category)

            if raw_search and not used_exact:
                if not provider_matches_search(provider, services, category, raw_search):
                    continue

            completed_qs = Booking.objects.filter(
                service__provider=provider,
                service__category=category,
                status='Completed',
            )
            total_bookings = Booking.objects.filter(
                service__provider=provider,
                service__category=category,
            ).count()

            provider_list.append({
                'provider': provider,
                'services': services,
                'total_bookings': total_bookings,
                'completed_bookings': completed_qs.count(),
                'total_earnings': sum(b.service.price for b in completed_qs),
            })

        add_ratings_to_provider_items(provider_list)
        company_groups = group_provider_items_by_company(provider_list)
        if company_groups:
            category_sections.append({
                'category': category,
                'collapse_prefix': f'sp-cat-{idx}',
                'company_groups': company_groups,
            })

    context = {
        'category_sections': category_sections,
        'search_query': raw_search,
    }
    return render(request, 'service_providers.html', context)


@login_required
def provider_customer_reviews(request, provider_id):
    """All customer ratings & reviews for a bookable service provider."""
    provider = get_object_or_404(
        User.objects.filter(is_provider=True).exclude(company_name=''),
        id=provider_id,
    )
    reviews = (
        ReviewRating.objects.filter(provider=provider, status=True)
        .select_related('customer', 'booking', 'booking__service')
        .order_by('-created_at')
    )
    rating_stats = ReviewRating.objects.filter(provider=provider, status=True).aggregate(
        avg=Avg('rating'),
        n=Count('id'),
    )
    context = {
        'provider': provider,
        'reviews': reviews,
        'review_avg': rating_stats['avg'],
        'review_count': rating_stats['n'] or 0,
    }
    return render(request, 'provider_customer_reviews.html', context)


@login_required
def service_detail(request, service_id):
    """Display service details with provider information"""
    service = get_object_or_404(
        Service.objects.select_related('provider').exclude(provider__company_name=''),
        id=service_id,
    )
    
    # Get provider statistics
    provider = service.provider
    provider_services = Service.objects.filter(provider=provider)
    total_bookings = Booking.objects.filter(service__provider=provider).count()
    completed_bookings = Booking.objects.filter(service__provider=provider, status='Completed').count()

    reviews_qs = (
        ReviewRating.objects.filter(provider=provider, status=True)
        .select_related('customer')
        .order_by('-created_at')[:25]
    )
    rating_stats = ReviewRating.objects.filter(provider=provider, status=True).aggregate(
        avg=Avg('rating'),
        n=Count('id'),
    )

    context = {
        'service': service,
        'provider': provider,
        'provider_services': provider_services,
        'total_bookings': total_bookings,
        'completed_bookings': completed_bookings,
        'provider_reviews': reviews_qs,
        'review_avg': rating_stats['avg'],
        'review_count': rating_stats['n'] or 0,
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


def plumbing_services(request):
    """Display plumbing services page"""
    return render(request, 'services/plumbing.html')


def electrical_services(request):
    """Display electrical services page"""
    return render(request, 'services/electrical.html')


def cleaning_services(request):
    """Display cleaning services page"""
    return render(request, 'services/cleaning.html')


def painting_services(request):
    """Display painting services page"""
    return render(request, 'services/painting.html')


def appliance_repair_services(request):
    """Display appliance repair services page"""
    return render(request, 'services/appliance_repair.html')


def handyman_services(request):
    """Display handyman services page"""
    return render(request, 'services/handyman.html')


def plumbing_providers(request):
    """Display plumbing service providers"""
    return get_category_providers(request, 'Plumbing', 'services/providers/plumbing_providers.html')


def electrical_providers(request):
    """Display electrical service providers"""
    return get_category_providers(request, 'Electrical', 'services/providers/electrical_providers.html')


def cleaning_providers(request):
    """Display cleaning service providers"""
    return get_category_providers(request, 'Cleaning', 'services/providers/cleaning_providers.html')


def painting_providers(request):
    """Display painting service providers"""
    return get_category_providers(request, 'Painting', 'services/providers/painting_providers.html')


def appliance_repair_providers(request):
    """Display appliance repair service providers"""
    return get_category_providers(request, 'Appliance Repair', 'services/providers/appliance_repair_providers.html')


def handyman_providers(request):
    """Display handyman service providers"""
    return get_category_providers(request, 'Handyman', 'services/providers/handyman_providers.html')


def get_category_providers(request, category, template):
    """Helper function to get providers for a specific service category"""
    providers = User.objects.filter(
        is_provider=True,
        service__category=category,
    ).exclude(company_name='').annotate(
        service_count=Count('service', filter=Q(service__category=category)),
        total_bookings=Count('service__booking', filter=Q(service__booking__service__category=category)),
        completed_bookings=Count('service__booking',
                                filter=Q(service__booking__service__category=category,
                                        service__booking__status='Completed')),
    ).distinct()

    search_query = request.GET.get('search', '').strip()
    provs_list = list(providers)
    used_exact = False
    if search_query:
        provs_list, used_exact = match_exact_username(provs_list, search_query.lower())

    provider_list = []
    for provider in provs_list:
        completed_bookings = Booking.objects.filter(
            service__provider=provider,
            service__category=category,
            status='Completed'
        )
        total_earnings = sum(booking.service.price for booking in completed_bookings)

        provider_list.append({
            'provider': provider,
            'services': Service.objects.filter(provider=provider, category=category),
            'total_bookings': provider.total_bookings,
            'completed_bookings': provider.completed_bookings,
            'total_earnings': total_earnings,
        })

    if search_query and not used_exact:
        provider_list = filter_providers_by_search(provider_list, search_query)

    add_ratings_to_provider_items(provider_list)
    company_groups = group_provider_items_by_company(provider_list)

    context = {
        'provider_list': provider_list,
        'company_groups': company_groups,
        'search_query': search_query,
        'category': category,
    }
    return render(request, template, context)


    