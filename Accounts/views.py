from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from .models import User
from Services.models import Service

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role = request.POST.get('role', '')

        # Validation
        error = None
        
        if not username:
            error = "Username is required."
        elif len(username) < 3:
            error = "Username must be at least 3 characters long."
        elif User.objects.filter(username=username).exists():
            error = "A user with that username already exists."
        elif not email:
            error = "Email is required."
        elif User.objects.filter(email=email).exists():
            error = "A user with that email already exists."
        elif not password:
            error = "Password is required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        elif not role or role not in ['customer', 'provider']:
            error = "Please select a valid role."

        if error:
            return render(request, 'register.html', {
                'error': error,
                'categories': Service.CATEGORY_CHOICES
            })

        try:
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            
            user = User.objects.create_user(username=username, email=email, password=password)
            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if role == 'customer':
                user.is_customer = True
            else:
                user.is_provider = True
            user.save()

            # If provider, create services
            if role == 'provider':
                service_names = request.POST.getlist('service_name')
                service_categories = request.POST.getlist('service_category')
                service_prices = request.POST.getlist('service_price')
                
                services_created = 0
                for i in range(len(service_names)):
                    service_name = service_names[i].strip()
                    service_category = service_categories[i]
                    service_price = service_prices[i]
                    
                    if service_name and service_category and service_price:
                        try:
                            price = int(service_price)
                            if price > 0:
                                Service.objects.create(
                                    name=service_name,
                                    category=service_category,
                                    price=price,
                                    provider=user
                                )
                                services_created += 1
                        except ValueError:
                            pass  # Skip invalid price

                if services_created > 0:
                    messages.success(request, f'Account created with {services_created} service(s)!')
                else:
                    messages.info(request, 'Account created! You can add services later from your profile.')

            login(request, user)
            if role == 'customer':
                messages.success(request, f'Account created successfully! Welcome, {username}!')
            return redirect('home')
        except Exception as e:
            return render(request, 'register.html', {
                'error': f'An error occurred: {str(e)}',
                'categories': Service.CATEGORY_CHOICES
            })

    return render(request, 'register.html', {
        'categories': Service.CATEGORY_CHOICES
    })

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

class CustomLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        # Redirect superusers to dashboard, others to home
        if self.request.user.is_superuser:
            return reverse_lazy('dashboard_home')
        return reverse_lazy('home')

@login_required
def profile(request):
    """Display user profile"""
    return render(request, 'profile.html', {'user': request.user})

@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        user = request.user
        
        # Update basic fields
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.phone_number = request.POST.get('phone_number', '').strip()
        user.address = request.POST.get('address', '').strip()
        
        # Handle profile picture upload
        if 'profile_picture' in request.FILES:
            user.profile_picture = request.FILES['profile_picture']
        
        # Validate email
        if user.email and User.objects.filter(email=user.email).exclude(id=user.id).exists():
            messages.error(request, 'This email is already in use by another account.')
            return render(request, 'edit_profile.html', {'user': user})
        
        try:
            user.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
    
    return render(request, 'edit_profile.html', {'user': request.user})

@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        user = request.user
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Validate old password
        if not user.check_password(old_password):
            messages.error(request, 'Your old password was entered incorrectly.')
            return render(request, 'change_password.html')
        
        # Validate new password
        if not new_password:
            messages.error(request, 'New password is required.')
            return render(request, 'change_password.html')
        
        if len(new_password) < 8:
            messages.error(request, 'New password must be at least 8 characters long.')
            return render(request, 'change_password.html')
        
        if new_password != confirm_password:
            messages.error(request, 'New password and confirmation password do not match.')
            return render(request, 'change_password.html')
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, user)
        
        messages.success(request, 'Your password was successfully updated!')
        return redirect('profile')
    
    return render(request, 'change_password.html')
