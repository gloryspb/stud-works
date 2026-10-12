from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "first_name", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Роль в сервисе", {"fields": ("role",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Роль в сервисе", {"fields": ("role", "email", "first_name")}),
    )
    search_fields = ("username", "email", "first_name", "last_name")
