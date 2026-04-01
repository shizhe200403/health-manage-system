from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AdminOperationLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("module", models.CharField(choices=[("users", "Users"), ("recipes", "Recipes"), ("community", "Community"), ("reports", "Reports")], max_length=32)),
                ("action", models.CharField(max_length=64)),
                ("target_type", models.CharField(blank=True, default="", max_length=64)),
                ("target_id", models.BigIntegerField(blank=True, null=True)),
                ("target_label", models.CharField(blank=True, default="", max_length=255)),
                ("summary", models.CharField(max_length=255)),
                ("changes", models.JSONField(blank=True, default=list)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "actor",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="admin_operation_logs", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "db_table": "admin_operation_log",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
