# Generated by Django 3.2.13 on 2022-09-21 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('slide', '0005_alter_pointer_annotated_slide'),
    ]

    operations = [
        migrations.AddField(
            model_name='slide',
            name='long_description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
