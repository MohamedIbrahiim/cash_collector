from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import os

from rest_framework.exceptions import ValidationError

User = get_user_model()


def is_frozen(user: User, raise_exception=False) -> bool:
    thresholds_days = os.environ.get("THRESHOLD_DAYS", 2)
    if (
        user.reached_limit_date
        and user.reached_limit_date + timedelta(days=thresholds_days) <= datetime.now()
    ):
        if raise_exception:
            raise ValidationError("You are frozen and can not collect any tasks")
        return True
    return False
