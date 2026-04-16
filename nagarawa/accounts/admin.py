from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'district', 'is_verified', 'is_staff', 'date_joined']
    list_filter = ['is_verified', 'is_staff', 'district']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'district']
    actions = ['verify_users']

    fieldsets = UserAdmin.fieldsets + (
        ('Profile', {'fields': ('avatar', 'bio', 'district', 'ward', 'phone', 'is_verified')}),
    )

    def verify_users(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f'{queryset.count()} users verified.')
    verify_users.short_description = "Mark selected users as verified"
