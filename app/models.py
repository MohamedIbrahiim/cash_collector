from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    manager = models.ForeignKey("self", on_delete=models.SET_NULL, null=True)
    reached_limit_date = models.DateTimeField(null=True)
    collected = models.FloatField(default=0)


class Task(models.Model):
    assigned_to = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="tasks"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(null=True)
    amount = models.FloatField()
    due_date = models.DateTimeField()
    collected_at = models.DateTimeField(null=True)
    is_collected = models.BooleanField(default=False)
    remaining_amount = models.FloatField(default=0)

    def __str__(self):
        return f"{self.assigned_to.get_username()} - {self.name} ({self.id})"
