from zoneinfo import ZoneInfo

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

KST = ZoneInfo("Asia/Seoul")


def preserve_existing_slots(apps, schema_editor):
    """이미 직접 가능 시간을 저장한 날은 '직접 설정한 날'로 표시해 기본값이 덮어쓰지 않게 한다."""
    Slot = apps.get_model("meetings", "AvailabilitySlot")
    Day = apps.get_model("meetings", "AvailabilityCustomDay")
    pairs = {
        (staff_id, start_at.astimezone(KST).date())
        for staff_id, start_at in Slot.objects.values_list("staff_id", "start_at")
    }
    Day.objects.bulk_create(
        [Day(staff_id=staff_id, day=day) for staff_id, day in sorted(pairs)], ignore_conflicts=True
    )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("meetings", "0003_confirmed_slot_unique"),
    ]

    operations = [
        migrations.CreateModel(
            name="AvailabilityCustomDay",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("day", models.DateField()),
                (
                    "staff",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="availabilitycustomday",
            constraint=models.UniqueConstraint(fields=("staff", "day"), name="uniq_staff_custom_day"),
        ),
        migrations.RunPython(preserve_existing_slots, migrations.RunPython.noop),
    ]
