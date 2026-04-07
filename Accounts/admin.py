from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username',
        'email',
        'company_name',
        'is_customer',
        'is_provider',
        'is_staff',
        'is_superuser',
    )
    list_filter = (*BaseUserAdmin.list_filter, 'is_customer', 'is_provider')
    search_fields = (*BaseUserAdmin.search_fields, 'company_name')

    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _('Home service'),
            {
                'fields': (
                    'is_customer',
                    'is_provider',
                    'company_name',
                    'phone_number',
                    'address',
                    'profile_picture',
                ),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'password1',
                    'password2',
                    'email',
                    'company_name',
                    'is_customer',
                    'is_provider',
                ),
            },
        ),
    )
