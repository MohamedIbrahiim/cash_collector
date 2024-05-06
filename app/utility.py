"""
Utility file to write methods

Writing any method that can be used twice
"""
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import os

from rest_framework.exceptions import ValidationError

from app.models import Task

User = get_user_model()


def is_frozen(user: User, raise_exception=False) -> bool:
    """
    Check if the user account is frozen based on a threshold of days.

    Args:
        user (User): The user object to check.
        raise_exception (bool): Whether to raise a ValidationError if the user is frozen (default: False).

    Returns:
        bool: True if the user is frozen, False otherwise.
    """
    thresholds_days = os.environ.get("THRESHOLD_DAYS", 2)
    if (
        user.reached_limit_date
        and user.reached_limit_date + timedelta(days=thresholds_days) <= datetime.now()
    ):
        if raise_exception:
            raise ValidationError("You are frozen and can not collect any tasks")
        return True
    return False


def collect_next_task(obj: Task, user: User, collect_date=None) -> None:
    """
    Collect the next task for a user and update user and task status.

    Args:
        obj: The task object to be collected.
        user (User): The user who is collecting the task.
        collect_date (datetime, optional): The date/time when the task is being collected.
            Defaults to None, which means the current datetime will be used.

    Raises:
        ValidationError: If the user account is frozen.

    """
    # adding custom date it could be inside parameter to be collect_date = datetime.now()
    # but it should be implemented outside so mocks can work correctly
    collect_date = collect_date if collect_date else datetime.now()
    is_frozen(user, raise_exception=True)
    obj.is_collected = True
    obj.collected_at = collect_date
    obj.save(update_fields=["is_collected", "collected_at"])
    user.collected += obj.amount
    if not user.reached_limit_date and user.collected >= os.environ.get(
        "THRESHOLD", 5000
    ):
        user.reached_limit_date = collect_date
    user.save()


def get_task(user: User, is_collected=False) -> Task:
    """
    Retrieve tasks assigned to a user based on collection status.

    Args:
        user (User): The user for whom to retrieve tasks.
        is_collected (bool, optional): Filter tasks by collection status (default: False).

    Returns:
        QuerySet: A queryset of Task objects filtered by user and collection status.
    """
    return Task.objects.filter(assigned_to=user, is_collected=is_collected)


def get_next_task(user: User) -> Task:
    """
    Retrieve the next task assigned to a user.

    Args:
        user (User): The user for whom to retrieve the next task.

    Returns:
        Task: The next task assigned to the user.

    Raises:
        ValidationError: If no tasks are assigned to the user.
    """
    next_task = get_task(user).order_by("id")[:1]
    if next_task.exists():
        return next_task[0]
    raise ValidationError("No assigned tasks")
