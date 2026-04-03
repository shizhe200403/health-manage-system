from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("recipes", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="recipe",
            name="is_premium",
            field=models.BooleanField(default=False),
        ),
    ]
