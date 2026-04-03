from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("community", "0004_comment_likes"),
    ]

    operations = [
        migrations.AddField(
            model_name="postcomment",
            name="parent_comment",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="replies", to="community.postcomment"),
        ),
    ]
