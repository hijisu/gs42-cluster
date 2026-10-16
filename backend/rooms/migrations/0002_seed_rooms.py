from django.db import migrations

ROOMS = [
    ("multipurpose", "다목적회의실", "", "TV"),
    ("universe-large", "유니버스룸(대)", "", "교육 공간"),
    ("universe-small", "유니버스룸(소)", "", "TV"),
]


def seed(apps, schema_editor):
    Room = apps.get_model("rooms", "Room")
    for order, (code, name, capacity, equipment) in enumerate(ROOMS, start=1):
        Room.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "capacity_note": capacity,
                "equipment": equipment,
                "status": "open",
                "sort_order": order,
            },
        )


def unseed(apps, schema_editor):
    apps.get_model("rooms", "Room").objects.filter(code__in=[r[0] for r in ROOMS]).delete()


class Migration(migrations.Migration):
    dependencies = [("rooms", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
