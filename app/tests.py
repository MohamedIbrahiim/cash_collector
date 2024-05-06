from unittest.mock import patch
from django.db.models import Sum
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from app.models import Task, User
from datetime import datetime, timedelta
from app.utility import is_frozen


class CashCollectorTest(TestCase):
    def setUp(self):
        self.manager = User.objects.create_superuser(
            "manager", "manager@example.com", "12345678"
        )
        self.cash_collector_obj = User.objects.create(
            username="cash_collector", email="cash@example.com", manager=self.manager
        )
        self.tasks = [
            Task.objects.create(
                assigned_to=self.cash_collector_obj,
                name=f"test-{i}",
                amount=1000,
                remaining_amount=1000,
                due_date=datetime.now(),
            )
            for i in range(1, 10)
        ]
        self.client = APIClient()
        self.client.force_authenticate(self.cash_collector_obj)

    def test_list_tasks_not_exists(self):
        response = self.client.get(reverse("get-tasks"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        query = Task.objects.filter(
            assigned_to=self.cash_collector_obj, is_collected=True
        )
        self.assertEqual(response.json().get("count"), query.count())

    def test_list_tasks(self):
        Task.objects.filter(pk__in=[self.tasks[0].id, self.tasks[1].id]).update(
            is_collected=True
        )
        response = self.client.get(reverse("get-tasks"), format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json().get("count"), 2)

    def test_next_task(self):
        response = self.client.get(reverse("get-next-tasks"), format="json")
        res_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res_json.get("id"),
            Task.objects.filter(assigned_to=self.cash_collector_obj, is_collected=False)
            .first()
            .id,
        )

    def test_no_next_task(self):
        Task.objects.filter(
            assigned_to=self.cash_collector_obj, is_collected=False
        ).update(is_collected=True)
        response = self.client.get(reverse("get-next-tasks"), format="json")
        res_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_json, ["No assigned tasks"])

    def test_collect_next_task(self):
        response = self.client.put(reverse("collect-tasks"))
        next_task_id = (
            Task.objects.filter(assigned_to=self.cash_collector_obj, is_collected=False)
            .first()
            .id
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(next_task_id, self.tasks[1].id)

    def test_collect_without_next_task(self):
        Task.objects.filter(
            assigned_to=self.cash_collector_obj, is_collected=False
        ).update(is_collected=True)
        response = self.client.put(reverse("collect-tasks"), format="json")
        res_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_json, ["No assigned tasks"])

    def test_collect_with_freeze(self):
        self.cash_collector_obj.reached_limit_date = datetime.now() - timedelta(days=2)
        response = self.client.put(reverse("collect-tasks"), format="json")
        res_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_json, ["You are frozen and can not collect any tasks"])

    def test_status_when_frozen(self):
        self.cash_collector_obj.reached_limit_date = datetime.now() - timedelta(days=2)
        response = self.client.get(reverse("check-status"), format="json")
        res_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(res_json.get("is_frozen"), True)

    def test_status_when_not_frozen(self):
        response = self.client.get(reverse("check-status"), format="json")
        res_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(res_json.get("is_frozen"), False)

    def test_pay_all(self):
        response = self.client.post(reverse("pay-all"), format="json")
        Task.objects.filter(
            assigned_to=self.cash_collector_obj, is_collected=False
        ).update(is_collected=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for element in Task.objects.filter(
            assigned_to=self.cash_collector_obj, is_collected=False
        ):
            self.assertEqual(element.remaining_amount, 0)

    def test_pay_some_with_invalid_amount(self):
        for _ in self.tasks:
            self.client.put(reverse("collect-tasks"))
        response = self.client.post(
            reverse("pay-some"), data={"collected": 100000}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), ["Invalid collected amount"])

    def test_pay_some_and_remove_frozen(self):
        with patch("app.utility.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime.now() - timedelta(days=2)
            for _ in self.tasks[:5]:
                self.client.put(reverse("collect-tasks"))
        self.assertEqual(is_frozen(self.cash_collector_obj), True)
        response = self.client.post(
            reverse("pay-some"), data={"collected": 1000}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(is_frozen(self.cash_collector_obj), False)

    def test_pay_some_and_no_more_to_collect(self):
        for _ in self.tasks[:5]:
            self.client.put(reverse("collect-tasks"))
        collected = Task.objects.filter(
            assigned_to=self.cash_collector_obj, is_collected=True
        ).aggregate(total_amount=Sum("amount"))["total_amount"]
        cash_collector_obj = User.objects.get(pk=self.cash_collector_obj.pk)
        self.assertEqual(cash_collector_obj.collected, collected)
        self.assertEqual(
            cash_collector_obj.reached_limit_date,
            Task.objects.filter(assigned_to=self.cash_collector_obj, is_collected=True)
            .order_by("-id")
            .first()
            .collected_at,
        )
        response = self.client.post(
            reverse("pay-some"), data={"collected": collected}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cash_collector_obj = User.objects.get(pk=self.cash_collector_obj.pk)
        self.assertEqual(cash_collector_obj.collected, 0)
        self.assertEqual(cash_collector_obj.reached_limit_date, None)
