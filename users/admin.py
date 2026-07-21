from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_approved', 'masjid', 'is_active')
    list_filter = ('role', 'is_approved', 'is_active')
    actions = ['approve_users']
    fieldsets = UserAdmin.fieldsets + (
        ('Masjid Role', {'fields': ('role', 'is_approved', 'masjid', 'phone')}),
    )

    def approve_users(self, request, queryset):
        queryset.update(is_approved=True)
    approve_users.short_description = 'Approve selected users'