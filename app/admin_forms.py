from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import Task
from django import forms

User = get_user_model()


class CustomUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["manager"].queryset = User.objects.filter(is_superuser=True)


class TaskAdminForm(forms.ModelForm):
    request = None

    class Meta:
        model = Task
        exclude = ["is_collected", "is_done", "collected_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # in case we want to show only assigned users to specific manager

        # self.fields["assigned_to"].queryset = User.objects.filter(
        #     manager=self.request.user
        # )

        self.fields["assigned_to"].queryset = User.objects.filter(is_superuser=False)
