from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import permissions, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.community.models import ContentReport, Post, PostComment
from apps.recipes.models import Recipe
from apps.tracking.models import MealRecord
from .models import ReportTask
from .services import generate_pdf_report, report_period

User = get_user_model()


class ReportPayloadSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField()
    end_date = serializers.DateField()


class EnvelopeReportPayloadSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportPayloadSerializer()


class ExportReportRequestSerializer(serializers.Serializer):
    report_type = serializers.ChoiceField(choices=["weekly", "monthly"], required=False)
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)


class ReportTaskDataSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    report_type = serializers.CharField()
    status = serializers.CharField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    generated_at = serializers.DateTimeField(allow_null=True)


class EnvelopeReportTaskSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportTaskDataSerializer()


class EnvelopeReportTaskListSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = ReportTaskDataSerializer(many=True)


class AdminUserMiniSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    nickname = serializers.CharField(allow_blank=True)
    display_name = serializers.CharField()


class AdminRecentReportTaskSerializer(serializers.Serializer):
    task_id = serializers.IntegerField()
    report_type = serializers.CharField()
    status = serializers.CharField()
    file_url = serializers.CharField(allow_blank=True)
    start_date = serializers.DateField(allow_null=True)
    end_date = serializers.DateField(allow_null=True)
    generated_at = serializers.DateTimeField(allow_null=True)
    user = AdminUserMiniSerializer()


class AdminOperationsSummarySerializer(serializers.Serializer):
    users_total = serializers.IntegerField()
    users_active = serializers.IntegerField()
    users_pending = serializers.IntegerField()
    recipes_total = serializers.IntegerField()
    recipes_pending = serializers.IntegerField()
    recipes_rejected = serializers.IntegerField()
    posts_total = serializers.IntegerField()
    posts_pending = serializers.IntegerField()
    posts_rejected = serializers.IntegerField()
    pending_reports = serializers.IntegerField()
    hidden_comments = serializers.IntegerField()
    meal_records_last_7_days = serializers.IntegerField()
    active_record_users_last_7_days = serializers.IntegerField()
    report_tasks_total = serializers.IntegerField()
    report_tasks_processing = serializers.IntegerField()
    report_tasks_failed = serializers.IntegerField()
    report_tasks_completed = serializers.IntegerField()


class AdminOperationsOverviewSerializer(serializers.Serializer):
    summary = AdminOperationsSummarySerializer()
    recent_tasks = AdminRecentReportTaskSerializer(many=True)


class EnvelopeAdminOperationsOverviewSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = AdminOperationsOverviewSerializer()


class IsAdminOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or user.is_staff or getattr(user, "role", "") in {"admin", "auditor"}))


def _build_report_response(user, report_type, start_date, end_date):
    task = ReportTask.objects.create(user=user, report_type=report_type, status="processing", start_date=start_date, end_date=end_date)
    try:
        file_path = generate_pdf_report(user, report_type, start_date, end_date)
        task.status = "completed"
        task.file_url = f"/media/reports/{file_path.name}"
        task.generated_at = timezone.now()
        task.save(update_fields=["status", "file_url", "generated_at", "updated_at"])
        return {
            "task_id": task.id,
            "file_url": task.file_url,
            "start_date": start_date,
            "end_date": end_date,
        }
    except Exception:
        task.status = "failed"
        task.save(update_fields=["status", "updated_at"])
        raise


class WeeklyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportPayloadSerializer)
    def get(self, request):
        try:
            start_date, end_date = report_period("weekly")
            return Response({"code": 0, "message": "success", "data": _build_report_response(request.user, "weekly", start_date, end_date)})
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class MonthlyReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportPayloadSerializer)
    def get(self, request):
        try:
            start_date, end_date = report_period("monthly")
            return Response({"code": 0, "message": "success", "data": _build_report_response(request.user, "monthly", start_date, end_date)})
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class ExportReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ExportReportRequestSerializer, responses=EnvelopeReportPayloadSerializer)
    def post(self, request):
        report_type = request.data.get("report_type", "weekly")
        if report_type not in {"weekly", "monthly"}:
            report_type = "weekly"
        start_date = request.data.get("start_date")
        end_date = request.data.get("end_date")
        if not start_date or not end_date:
            start_date, end_date = report_period(report_type)
        else:
            try:
                start_date = date.fromisoformat(str(start_date))
                end_date = date.fromisoformat(str(end_date))
            except ValueError:
                return Response({"code": 400, "message": "invalid date format", "data": None}, status=400)
        try:
            data = _build_report_response(request.user, report_type, start_date, end_date)
            return Response({"code": 0, "message": "success", "data": data}, status=status.HTTP_201_CREATED)
        except Exception:
            return Response({"code": 500, "message": "report generation failed", "data": None}, status=500)


class ReportTaskView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name="task_id", location=OpenApiParameter.PATH, required=True, type=OpenApiTypes.INT)],
        responses=EnvelopeReportTaskSerializer,
    )
    def get(self, request, task_id):
        task = ReportTask.objects.filter(id=task_id, user=request.user).first()
        if task is None:
            return Response({"code": 404, "message": "not found", "data": None}, status=404)
        return Response(
            {
                "code": 0,
                "message": "success",
                "data": {
                    "task_id": task.id,
                    "report_type": task.report_type,
                    "status": task.status,
                    "file_url": task.file_url,
                    "start_date": task.start_date,
                    "end_date": task.end_date,
                    "generated_at": task.generated_at,
                },
            }
        )


class ReportTaskListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses=EnvelopeReportTaskListSerializer)
    def get(self, request):
        tasks = ReportTask.objects.filter(user=request.user).order_by("-created_at")[:10]
        data = [
            {
                "task_id": task.id,
                "report_type": task.report_type,
                "status": task.status,
                "file_url": task.file_url,
                "start_date": task.start_date,
                "end_date": task.end_date,
                "generated_at": task.generated_at,
            }
            for task in tasks
        ]
        return Response({"code": 0, "message": "success", "data": data})


class AdminOperationsOverviewView(APIView):
    permission_classes = [IsAdminOperator]

    @extend_schema(responses=EnvelopeAdminOperationsOverviewSerializer)
    def get(self, request):
        today = timezone.localdate()
        last_week = today - timedelta(days=6)

        recent_tasks_qs = (
            ReportTask.objects.select_related("user")
            .order_by("-created_at", "-id")[:8]
        )
        recent_tasks = [
            {
                "task_id": task.id,
                "report_type": task.report_type,
                "status": task.status,
                "file_url": task.file_url,
                "start_date": task.start_date,
                "end_date": task.end_date,
                "generated_at": task.generated_at,
                "user": {
                    "id": task.user_id,
                    "username": task.user.username,
                    "nickname": task.user.nickname,
                    "display_name": task.user.nickname or task.user.username,
                },
            }
            for task in recent_tasks_qs
        ]

        meal_record_stats = MealRecord.objects.filter(record_date__gte=last_week).aggregate(
            total=Count("id"),
            users=Count("user_id", distinct=True),
        )

        summary = {
            "users_total": User.objects.count(),
            "users_active": User.objects.filter(status="active").count(),
            "users_pending": User.objects.filter(status="pending").count(),
            "recipes_total": Recipe.objects.exclude(status="archived").count(),
            "recipes_pending": Recipe.objects.exclude(status="archived").filter(audit_status="pending").count(),
            "recipes_rejected": Recipe.objects.exclude(status="archived").filter(audit_status="rejected").count(),
            "posts_total": Post.objects.exclude(status="archived").count(),
            "posts_pending": Post.objects.exclude(status="archived").filter(audit_status="pending").count(),
            "posts_rejected": Post.objects.exclude(status="archived").filter(audit_status="rejected").count(),
            "pending_reports": ContentReport.objects.filter(status="pending").count(),
            "hidden_comments": PostComment.objects.filter(status="hidden").count(),
            "meal_records_last_7_days": meal_record_stats["total"] or 0,
            "active_record_users_last_7_days": meal_record_stats["users"] or 0,
            "report_tasks_total": ReportTask.objects.count(),
            "report_tasks_processing": ReportTask.objects.filter(status="processing").count(),
            "report_tasks_failed": ReportTask.objects.filter(status="failed").count(),
            "report_tasks_completed": ReportTask.objects.filter(status="completed").count(),
        }

        return Response({"code": 0, "message": "success", "data": {"summary": summary, "recent_tasks": recent_tasks}})
