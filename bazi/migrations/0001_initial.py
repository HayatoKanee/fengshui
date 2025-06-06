# Generated by Django 5.2.1 on 2025-05-22 04:06

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="姓名")),
                ("birth_year", models.IntegerField(verbose_name="出生年")),
                ("birth_month", models.IntegerField(verbose_name="出生月")),
                ("birth_day", models.IntegerField(verbose_name="出生日")),
                ("birth_hour", models.IntegerField(verbose_name="出生时")),
                ("birth_minute", models.IntegerField(verbose_name="出生分")),
                ("is_male", models.BooleanField(default=True, verbose_name="性别")),
                (
                    "is_default",
                    models.BooleanField(default=False, verbose_name="默认资料"),
                ),
                (
                    "is_day_master_strong",
                    models.BooleanField(blank=True, null=True, verbose_name="日主强"),
                ),
                (
                    "day_master_wuxing",
                    models.CharField(
                        blank=True, max_length=10, null=True, verbose_name="日主五行"
                    ),
                ),
                (
                    "favorable_wuxing",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="有利五行"
                    ),
                ),
                (
                    "unfavorable_wuxing",
                    models.CharField(
                        blank=True, max_length=50, null=True, verbose_name="不利五行"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profiles",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "用户八字资料",
                "verbose_name_plural": "用户八字资料",
                "ordering": ["-created_at"],
            },
        ),
    ]
