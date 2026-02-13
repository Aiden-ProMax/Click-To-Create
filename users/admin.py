from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    inlines = [UserProfileInline]
    list_display = ("username", "email", "is_staff", "is_superuser", "is_active", "last_login", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "radicale_username")
    search_fields = ("user__username", "user__email", "radicale_username")
