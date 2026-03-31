from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import ContentReport, Post, PostComment

User = get_user_model()


class UserBriefSerializer(serializers.ModelSerializer):
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "nickname", "avatar_url", "display_name"]

    def get_display_name(self, obj):
        return obj.nickname or obj.username


class PostCommentSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = PostComment
        fields = ["id", "user", "user_info", "content", "status", "created_at"]
        read_only_fields = ["id", "status", "created_at", "user"]


class AdminPostCommentSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = PostComment
        fields = ["id", "user", "user_info", "content", "status", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "user_info", "created_at", "updated_at"]


class PostSerializer(serializers.ModelSerializer):
    comments = serializers.SerializerMethodField()
    user_info = UserBriefSerializer(source="user", read_only=True)

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "status",
            "audit_status",
            "comments",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "audit_status", "created_at", "updated_at", "comments"]

    def get_comments(self, obj):
        comments = obj.comments.filter(status="visible").select_related("user")
        return PostCommentSerializer(comments, many=True).data

    def create(self, validated_data):
        return Post.objects.create(user=self.context["request"].user, **validated_data)


class AdminPostListSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)
    visible_comment_count = serializers.SerializerMethodField()
    hidden_comment_count = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()
    latest_report_status = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "status",
            "audit_status",
            "created_at",
            "updated_at",
            "visible_comment_count",
            "hidden_comment_count",
            "report_count",
            "latest_report_status",
        ]

    def get_visible_comment_count(self, obj):
        return obj.comments.filter(status="visible").count()

    def get_hidden_comment_count(self, obj):
        return obj.comments.filter(status="hidden").count()

    def get_report_count(self, obj):
        return ContentReport.objects.filter(target_type="post", target_id=obj.id).count()

    def get_latest_report_status(self, obj):
        latest = ContentReport.objects.filter(target_type="post", target_id=obj.id).order_by("-created_at").first()
        return latest.status if latest else ""


class AdminPostDetailSerializer(serializers.ModelSerializer):
    user_info = UserBriefSerializer(source="user", read_only=True)
    comments = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id",
            "user",
            "user_info",
            "title",
            "content",
            "cover_image_url",
            "status",
            "audit_status",
            "comments",
            "report_count",
            "created_at",
            "updated_at",
        ]

    def get_comments(self, obj):
        comments = obj.comments.select_related("user").order_by("-created_at")
        return AdminPostCommentSerializer(comments, many=True).data

    def get_report_count(self, obj):
        return ContentReport.objects.filter(target_type="post", target_id=obj.id).count()


class AdminPostUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ["title", "content", "cover_image_url", "status", "audit_status"]


class ContentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReport
        fields = ["id", "target_type", "target_id", "reason", "status", "processed_by", "processed_at", "created_at"]
        read_only_fields = ["id", "status", "processed_by", "processed_at", "created_at"]
        extra_kwargs = {
            "target_type": {"required": False},
            "target_id": {"required": False},
        }

    def create(self, validated_data):
        return ContentReport.objects.create(reporter=self.context["request"].user, **validated_data)


class AdminContentReportListSerializer(serializers.ModelSerializer):
    reporter_info = UserBriefSerializer(source="reporter", read_only=True)
    processed_by_info = UserBriefSerializer(source="processed_by", read_only=True)
    target_post_title = serializers.SerializerMethodField()

    class Meta:
        model = ContentReport
        fields = [
            "id",
            "reporter",
            "reporter_info",
            "target_type",
            "target_id",
            "target_post_title",
            "reason",
            "status",
            "processed_by",
            "processed_by_info",
            "processed_at",
            "created_at",
        ]

    def get_target_post_title(self, obj):
        if obj.target_type != "post":
            return ""
        post = Post.objects.filter(id=obj.target_id).only("title").first()
        return post.title if post else ""


class AdminContentReportDetailSerializer(AdminContentReportListSerializer):
    target_post = serializers.SerializerMethodField()

    class Meta(AdminContentReportListSerializer.Meta):
        fields = AdminContentReportListSerializer.Meta.fields + ["target_post"]

    def get_target_post(self, obj):
        if obj.target_type != "post":
            return None
        post = Post.objects.select_related("user").prefetch_related("comments__user").filter(id=obj.target_id).first()
        return AdminPostDetailSerializer(post).data if post else None


class AdminContentReportUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentReport
        fields = ["status"]
