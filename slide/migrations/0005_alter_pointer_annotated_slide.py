# Generated by Django 3.2 on 2021-09-22 11:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('slide', '0004_slide_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pointer',
            name='annotated_slide',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slide.annotatedslide'),
        ),
    ]