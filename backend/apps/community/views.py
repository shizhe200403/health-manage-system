from django.utils import timezone
from django.db import models
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.views import APIView

from apps.common.views import EnvelopeModelViewSet
from .models import ContentReport, Post, PostComment
from .serializers import (
    AdminContentReportDetailSerializer,
    AdminContentReportListSerializer,
    AdminContentReportUpdateSerializer,
    AdminPostDetailSerializer,
    AdminPostListSerializer,
    AdminPostUpdateSerializer,
    ContentReportSerializer,
    PostCommentSerializer,
    PostSerializer,
)


class PostViewSet(EnvelopeModelViewSet):
    queryset = Post.objects.none()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Post.objects.none()
        user = self.request.user
        return Post.objects.select_related("user").prefetch_related("comments", "comments__user").filter(
            models.Q(status="published") | models.Q(user=user)
        )

    def perform_create(self, serializer):
        serializer.save()

    def perform_update(self, serializer):
        post = serializer.instance
        if post.user_id != self.request.user.id and getattr(self.request.user, "role", "") not in {"admin", "auditor"}:
            raise PermissionDenied("只有作者或管理员可以编辑帖子")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.user_id != request.user.id and getattr(request.user, "role", "") not in {"admin", "auditor"}:
            return Response({"code": 403, "message": "forbidden", "data": None}, status=403)
        post.status = "archived"
        post.save(update_fields=["status", "updated_at"])
        return Response({"code": 0, "message": "success", "data": {"archived": True}})

    @action(detail=True, methods=["post"])
    def comments(self, request, pk=None):
        post = self.get_object()
        serializer = PostCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = PostComment.objects.create(post=post, user=request.user, **serializer.validated_data)
        return Response({"code": 0, "message": "success", "data": PostCommentSerializer(comment).data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def report(self, request, pk=None):
        post = self.get_object()
        serializer = ContentReportSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        report = serializer.save(target_type="post", target_id=post.id)
        return Response({"code": 0, "message": "success", "data": ContentReportSerializer(report).data}, status=status.HTTP_201_CREATED)


@extend_schema_view(
    destroy=extend_schema(
        responses=inline_serializer(
            name="EnvelopeCommentModerationSerializer",
            fields={
                "code": serializers.IntegerField(),
                "message": serializers.CharField(),
                "data": serializers.JSONField(),
            },
        )
    )
)
class CommentModerationViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, pk=None):
        if getattr(request.user, "role", "") not in {"admin", "auditor"}:
            return Response({"code": 403, "message": "forbidden", "data": None}, status=403)
        comment = PostComment.objects.filter(id=pk).first()
        if comment is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        comment.status = "hidden"
        comment.save(update_fields=["status", "updated_at"])
        return Response({"code": 0, "message": "success", "data": {"hidden": True}})


class ContentReportViewSet(EnvelopeModelViewSet):
    queryset = ContentReport.objects.none()
    serializer_class = ContentReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return ContentReport.objects.none()
        return ContentReport.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        serializer.save()


class IsAdminModerator(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, "role", "") in {"admin", "auditor"}))


class AdminPostPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50

    def get_paginated_response(self, data):
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "count": self.page.paginator.count,
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link(),
                    "items": data,
                },
            }
        )


class AdminContentReportPagination(AdminPostPagination):
    pass


class AdminPostListEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminPostListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "items": AdminPostListSerializer(many=True),
        },
    )


class AdminPostDetailEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminPostDetailSerializer()


class AdminContentReportListEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = inline_serializer(
        name="AdminContentReportListData",
        fields={
            "count": serializers.IntegerField(),
            "next": serializers.CharField(allow_null=True),
            "previous": serializers.CharField(allow_null=True),
            "items": AdminContentReportListSerializer(many=True),
        },
    )


class AdminContentReportDetailEnvelopeSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminContentReportDetailSerializer()


class AdminCommunityPostListView(APIView):
    permission_classes = [IsAdminModerator]
    pagination_class = AdminPostPagination

    @extend_schema(responses=AdminPostListEnvelopeSerializer)
    def get(self, request):
        queryset = Post.objects.select_related("user").prefetch_related("comments").order_by("-updated_at", "-id")

        keyword = request.query_params.get("keyword", "").strip()
        status_value = request.query_params.get("status", "").strip()
        audit_status = request.query_params.get("audit_status", "").strip()
        author = request.query_params.get("author", "").strip()

        if keyword:
            queryset = queryset.filter(models.Q(title__icontains=keyword) | models.Q(content__icontains=keyword))
        if status_value:
            queryset = queryset.filter(status=status_value)
        if audit_status:
            queryset = queryset.filter(audit_status=audit_status)
        if author:
            queryset = queryset.filter(
                models.Q(user__username__icontains=author)
                | models.Q(user__nickname__icontains=author)
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminPostListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminCommunityPostDetailView(APIView):
    permission_classes = [IsAdminModerator]

    def get_object(self, post_id):
        return get_object_or_404(Post.objects.select_related("user").prefetch_related("comments__user"), pk=post_id)

    @extend_schema(responses=AdminPostDetailEnvelopeSerializer)
    def get(self, request, post_id):
        post = self.get_object(post_id)
        serializer = AdminPostDetailSerializer(post)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    @extend_schema(request=AdminPostUpdateSerializer, responses=AdminPostDetailEnvelopeSerializer)
    def patch(self, request, post_id):
        post = self.get_object(post_id)
        serializer = AdminPostUpdateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        detail = AdminPostDetailSerializer(post)
        return Response({"code": 0, "message": "success", "data": detail.data}, status=status.HTTP_200_OK)


class AdminContentReportListView(APIView):
    permission_classes = [IsAdminModerator]
    pagination_class = AdminContentReportPagination

    @extend_schema(responses=AdminContentReportListEnvelopeSerializer)
    def get(self, request):
        queryset = ContentReport.objects.select_related("reporter", "processed_by").order_by("-created_at", "-id")

        keyword = request.query_params.get("keyword", "").strip()
        status_value = request.query_params.get("status", "").strip()
        target_type = request.query_params.get("target_type", "").strip()

        if status_value:
            queryset = queryset.filter(status=status_value)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if keyword:
            queryset = queryset.filter(
                models.Q(reason__icontains=keyword)
                | models.Q(reporter__username__icontains=keyword)
                | models.Q(reporter__nickname__icontains=keyword)
            )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        serializer = AdminContentReportListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class AdminContentReportDetailView(APIView):
    permission_classes = [IsAdminModerator]

    def get_object(self, report_id):
        return get_object_or_404(ContentReport.objects.select_related("reporter", "processed_by"), pk=report_id)

    @extend_schema(responses=AdminContentReportDetailEnvelopeSerializer)
    def get(self, request, report_id):
        report = self.get_object(report_id)
        serializer = AdminContentReportDetailSerializer(report)
        return Response({"code": 0, "message": "success", "data": serializer.data})

    @extend_schema(request=AdminContentReportUpdateSerializer, responses=AdminContentReportDetailEnvelopeSerializer)
    def patch(self, request, report_id):
        report = self.get_object(report_id)
        serializer = AdminContentReportUpdateSerializer(report, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        report = serializer.save(
            processed_by=request.user if serializer.validated_data.get("status") in {"processed", "rejected"} else None,
            processed_at=timezone.now() if serializer.validated_data.get("status") in {"processed", "rejected"} else None,
        )
        detail = AdminContentReportDetailSerializer(report)
        return Response({"code": 0, "message": "success", "data": detail.data}, status=status.HTTP_200_OK)
