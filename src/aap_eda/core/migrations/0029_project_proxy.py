# Generated by Django 4.2.7 on 2024-04-11 15:03

from django.db import migrations

import aap_eda.core.utils.crypto.fields


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0028_remove_activation_credentials_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="proxy",
            field=aap_eda.core.utils.crypto.fields.EncryptedTextField(
                blank=True, default=""
            ),
        ),
    ]
