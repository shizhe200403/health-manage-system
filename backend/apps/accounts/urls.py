from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AdminUserDetailView, AdminUserListView, FullProfileView, HealthConditionView, LoginView, MeView, ProfileView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("me/", MeView.as_view(), name="me"),
    path("me/profile/", ProfileView.as_view(), name="me-profile"),
    path("me/health-condition/", HealthConditionView.as_view(), name="me-health-condition"),
    path("me/full-profile/", FullProfileView.as_view(), name="me-full-profile"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/", AdminUserDetailView.as_view(), name="admin-user-detail"),
]
