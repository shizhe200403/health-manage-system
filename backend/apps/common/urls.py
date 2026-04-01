from django.urls import path

from .views import AdminOperationLogListView, HealthCheckView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("admin/operation-logs/", AdminOperationLogListView.as_view(), name="admin-operation-logs"),
]
