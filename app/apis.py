import os
from django.contrib.auth import get_user_model
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
    CustomCollectSerializer,
)
from .utility import is_frozen, collect_next_task, get_task, get_next_task

User = get_user_model()


class GetDoneTasks(ListAPIView):
    """
    Retrieve the tasks that have been collected by the user.

    API endpoint to retrieve the tasks that have been collected by the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ReadTaskSerializer

    def get_queryset(self):
        return get_task(self.request.user, is_collected=True)


class GetNextTask(RetrieveAPIView):
    """
    Retrieve the next task assigned to the user.

    API endpoint to retrieve the next task assigned to the authenticated user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ReadTaskSerializer
    queryset = Task.objects.all()

    def get_object(self):
        return get_next_task(self.request.user)


class CollectTask(UpdateAPIView):
    """
    Collect Task API endpoint.

    API endpoint for collecting the next task if it exists and the user is not frozen.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = None
    queryset = None
    user = None

    def get_object(self):
        return get_next_task(self.request.user)

    def update(self, request, *args, **kwargs):
        collect_next_task(self.get_object(), request.user)
        return Response(status=status.HTTP_200_OK)


class CustomCollectTask(CollectTask):
    """
    Custom Collect Task API endpoint.

    API endpoint for collecting the next task if it exists and the user is not frozen,
    with customization to test the frozen flow by adding a custom date.
    """

    serializer_class = CustomCollectSerializer

    def update(self, request, *args, **kwargs):
        data = request.data
        self.serializer_class(data=data).is_valid(raise_exception=True)
        collect_next_task(self.get_object(), request.user, data.get("collect_date"))
        return Response(status=status.HTTP_200_OK)


class CheckStatus(RetrieveAPIView):
    """
    Check User Status API endpoint.

    API endpoint to check if the authenticated user is frozen.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = IsFrozenSerializer
    queryset = None

    def retrieve(self, request, *args, **kwargs):
        return Response(
            {"is_frozen": is_frozen(request.user)}, status=status.HTTP_200_OK
        )


class PayAllCollected(CreateAPIView):
    """
    Pay All Collected API endpoint.

    API endpoint to reset the collected amount and remaining amounts of tasks for the user.
    """

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
    Pay Some of Collected API endpoint.

    API endpoint to pay a portion of the collected amount and update remaining amounts of tasks.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = PaySomeCollectedSerializer
    queryset = None

    @classmethod
    def get_freeze_task_date(cls, task_id):
        # Get remaining tasks with IDs greater than the given task_id
        remaining_tasks = Task.objects.filter(pk__gt=task_id)
        total_amount = 0
        # Calculate the total amount of remaining tasks
        for task in remaining_tasks:
            total_amount += task.amount
            # Check if the task amount equals the threshold amount
            if task.amount == os.environ.get("THRESHOLD", 5000):
                # Return the collected_at date of the task that reached the threshold
                # to count the freeze time after
                return task.collected_at

    def pay_some_tasks(self, user, tasks, collected):
        updated_tasks = []
        # Iterate through tasks to update their remaining amounts
        for task in tasks:
            updated_tasks.append(task)
            if task.remaining_amount <= collected:
                # If the remaining amount of the task is less than or equal to the collected amount,
                # set remaining_amount to 0 and reduce collected by the remaining amount
                collected -= task.remaining_amount
                task.remaining_amount = 0
            else:
                # If the remaining amount of the task is greater than the collected amount,
                # subtract the collected amount from the remaining amount and break the loop
                task.remaining_amount -= collected

                # Check if user's total collected amount reaches or exceeds the threshold
                if user.collected >= os.environ.get("THRESHOLD", 5000):
                    # Set the reached_limit_date to the date of the task that reached the threshold
                    user.reached_limit_date = self.get_freeze_task_date(task.id)
                break
        return updated_tasks

    def create(self, request, *args, **kwargs):
        body = request.data
        # Validate the input data using the serializer
        self.serializer_class(data=body).is_valid(raise_exception=True)
        collected = body.get("collected")
        # Check if the collected amount is valid
        if request.user.collected == 0 or collected > request.user.collected:
            raise ValidationError("Invalid collected amount")
        # Deduct the collected amount from the user's total collected amount
        request.user.collected -= collected
        # Get all tasks with remaining amounts and assigned to the user
        tasks = Task.objects.filter(
            remaining_amount__gt=0, assigned_to=request.user
        ).order_by("id")
        # Update the tasks' remaining amounts based on the collected amount
        updated_tasks = self.pay_some_tasks(request.user, tasks, collected)
        # Reset reached_limit_date if user's collected amount falls below the threshold
        if request.user.collected < os.environ.get("THRESHOLD", 5000):
            request.user.reached_limit_date = None
        request.user.save()
        # Bulk update the remaining amounts of tasks
        Task.objects.bulk_update(updated_tasks, ["remaining_amount"])
        return Response(status=status.HTTP_200_OK)
