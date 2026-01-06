from django.urls import path
from .views import register, logout_view, CustomLoginView, profile, edit_profile, change_password

urlpatterns = [
    path('register/', register, name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/change-password/', change_password, name='change_password'),
]
