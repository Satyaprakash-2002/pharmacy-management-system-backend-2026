
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("branches", "0002_alter_branch_address_alter_branch_phone"),
        ("subscriptions", "0004_remove_subscription_retailer_subscription_branch_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="branch",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subscriptions",
                to="branches.branch",
            ),
        ),
    ]
