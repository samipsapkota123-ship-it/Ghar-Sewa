from django.contrib.auth.models import AbstractUser
from django.db import models
import os

def user_profile_picture_path(instance, filename):
    """Generate file path for user profile pictures"""
    ext = filename.split('.')[-1]
    filename = f'profile_{instance.id}_{instance.username}.{ext}'
    return os.path.join('profile_pictures', filename)

class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_provider = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to=user_profile_picture_path, blank=True, null=True, help_text="Profile picture")
    phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="Phone number")
    address = models.TextField(blank=True, null=True, help_text="Address")
    
    def __str__(self):
        return self.username
