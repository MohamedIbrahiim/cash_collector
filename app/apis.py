import os
from datetime import datetime
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    ListAPIView,
    UpdateAPIView,
    RetrieveAPIView,
    CreateAPIView,
)
from rest_framework.response import Response

from .models import Task
from .serializers import (
    ReadTaskSerializer,
    EmptySerializer,
    IsFrozenSerializer,
    PaySomeCollectedSerializer,
)
from .utility import is_frozen


class GetDoneTasks(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReadTaskSerializer

    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user, is_collected=True)


class GetNextTask(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReadTaskSerializer
    queryset = Task.objects.filter(is_collected=False).order_by("id")[:1]

    def get_object(self):
        query = Task.objects.filter(
            is_collected=False, assigned_to=self.request.user
        ).order_by("id")[:1]
        if query.exists():
            return self.get_queryset()[0]
        raise ValidationError("You do not have any tasks")


class CollectTask(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmptySerializer
    queryset = None
    user = None

    def get_object(self):
        self.user = self.request.user
        # To validate if we are updating next task
        next_task = Task.objects.filter(
            is_collected=False, assigned_to=self.request.user
        ).order_by("id")[:1]
        if next_task.exists():
            return next_task[0]
        raise ValidationError("No assigned tasks")

    def update(self, request, *args, **kwargs):
        obj = self.get_object()
        is_frozen(self.user, raise_exception=True)
        obj.is_collected = True
        obj.collected_at = datetime.now()
        obj.save(update_fields=["is_collected", "collected_at"])
        self.user.collected += obj.amount
        if not self.user.reached_limit_date and self.user.collected >= os.environ.get(
            "THRESHOLD", 5000
        ):
            self.user.reached_limit_date = obj.collected_at
        self.user.save()
        return Response(status=status.HTTP_200_OK)


class CheckStatus(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = IsFrozenSerializer
    queryset = None

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"is_frozen": is_frozen(request.user)}, status=status.HTTP_200_OK
        )


class PayAllCollected(CreateAPIView):
    serializer_class = EmptySerializer
    queryset = None

    def create(self, request, *args, **kwargs):
        request.user.collected = 0
        request.user.reached_limit_date = None
        request.user.save(update_fields=["collected", "reached_limit_date"])
        Task.objects.filter(remaining_amount__gt=0, assigned_to=request.user).update(
            remaining_amount=0
        )
        return Response(status=status.HTTP_200_OK)


class PaySomeOfCollected(CreateAPIView):
    """
    Pay some of collected money

    ex:
    - if we collected 6000, and we paid 1000 we will still freeze,
    5000 -> 0 -> 2000 -> date
    # 5000 -- 2000 -- 2000 -- 2000 => 2 Freezed
    - if we collected 6000, and we paid 2000 we will not be frozen but 4000 will be left,
    - if we collected 6000, and we paid 6000 we will not be frozen and left amount will be 0
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PaySomeCollectedSerializer
    queryset = None

    @classmethod
    def get_freeze_task_date(cls, task_id):
        remaining_tasks = Task.objects.filter(pk__gt=task_id)
        total_amount = 0
        for task in remaining_tasks:
            total_amount += task.amount
            if task.amount == os.environ.get("THRESHOLD", 5000):
                return task.collected_at

    def create(self, request, *args, **kwargs):
        body = request.data
        self.serializer_class(data=body).is_valid(raise_exception=True)
        collected = body.get("collected")
        if request.user.collected == 0 or collected > request.user.collected:
            raise ValidationError("invalid collected amount")
        request.user.collected -= collected
        tasks = Task.objects.filter(
            remaining_amount__gt=0, assigned_to=request.user
        ).order_by("id")
        updated_tasks = []
        for task in tasks:
            updated_tasks.append(task)
            if task.remaining_amount <= collected:
                collected -= task.remaining_amount
                task.remaining_amount = 0
            else:
                task.remaining_amount -= collected

                if request.user.collected >= os.environ.get("THRESHOLD", 5000):
                    request.user.reached_limit_date = self.get_freeze_task_date(task.id)
                break
        if request.user.collected < os.environ.get("THRESHOLD", 5000):
            request.user.reached_limit_date = None
        request.user.save()
        Task.objects.bulk_update(updated_tasks, ["remaining_amount"])
        return Response(status=status.HTTP_200_OK)
