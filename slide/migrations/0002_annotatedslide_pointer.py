# Generated by Django 3.2 on 2021-09-01 08:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('slide', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnnotatedSlide',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slide', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='slide.slide')),
            ],
        ),
        migrations.CreateModel(
            name='Pointer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_x', models.FloatField()),
                ('position_y', models.FloatField()),
                ('text', models.CharField(max_length=256)),
                ('annotated_slide', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='slide.annotatedslide')),
            ],
        ),
    ]
