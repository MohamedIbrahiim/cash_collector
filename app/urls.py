from django.urls import path
from .apis import (
    GetDoneTasks,
    GetNextTask,
    CollectTask,
    CustomCollectTask,
    CheckStatus,
    PayAllCollected,
    PaySomeOfCollected,
)

urlpatterns = [
    path("tasks/", GetDoneTasks.as_view(), name="get-tasks"),
    path("next-task/", GetNextTask.as_view(), name="get-next-tasks"),
    path("collect/", CollectTask.as_view(), name="collect-tasks"),
    path("custom/collect/", CustomCollectTask.as_view(), name="custom-collect-tasks"),
    path("status/", CheckStatus.as_view(), name="check-status"),
    path("pay/all/", PayAllCollected.as_view(), name="pay-all"),
    path("pay/some/", PaySomeOfCollected.as_view(), name="pay-some"),
]
