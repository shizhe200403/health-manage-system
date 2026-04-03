from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0003_user_security_question")]

    operations = [
        migrations.AddField(
            model_name="user",
            name="plan",
            field=models.CharField(
                choices=[("free", "免费版"), ("pro", "Pro 版")],
                default="free",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="user",
            name="ai_monthly_usage",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="user",
            name="ai_usage_reset_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
