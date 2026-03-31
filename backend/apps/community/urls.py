from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AdminCommunityPostDetailView,
    AdminCommunityPostListView,
    AdminContentReportDetailView,
    AdminContentReportListView,
    CommentModerationViewSet,
    ContentReportViewSet,
    PostViewSet,
)

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="post")
router.register(r"content-reports", ContentReportViewSet, basename="content-report")

urlpatterns = router.urls + [
    path("comments/<int:pk>/", CommentModerationViewSet.as_view({"delete": "destroy"}), name="comment-hide"),
    path("community/admin/posts/", AdminCommunityPostListView.as_view(), name="admin-community-posts"),
    path("community/admin/posts/<int:post_id>/", AdminCommunityPostDetailView.as_view(), name="admin-community-post-detail"),
    path("community/admin/reports/", AdminContentReportListView.as_view(), name="admin-community-reports"),
    path("community/admin/reports/<int:report_id>/", AdminContentReportDetailView.as_view(), name="admin-community-report-detail"),
]
