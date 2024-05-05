from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .admin_forms import CustomUserForm, TaskAdminForm
from .models import Task

User = get_user_model()


class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email", "manager")}),
        ("Permissions", {"fields": ("is_active", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "manager",
                    "is_superuser",
                ),
            },
        ),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_superuser")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    form = CustomUserForm


class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    readonly_fields = ["is_collected", "collected_at", "remaining_amount"]

    def save_model(self, request, obj, form, change):
        # Calculate the remaining amount based on the amount being added
        remaining_amount = obj.amount
        obj.remaining_amount = remaining_amount
        super().save_model(request, obj, form, change)

    # in case we need to send manager inside request to see only his managed cash collectors

    # def get_form(self, request, obj=None, **kwargs):
    #     form = super().get_form(request, obj, **kwargs)
    #     form.request = request
    #     return form


admin.site.register(User, CustomUserAdmin)
admin.site.register(Task, TaskAdmin)
