from django.db import migrations

TYPES = [
    ("freeze", "프리즈"),
    ("other-program", "타 사업 참여"),
    ("dormitory", "기숙사 이용"),
    ("assignment", "과제"),
    ("military", "예비군·병무"),
    ("other", "기타"),
]


def seed(apps, schema_editor):
    MeetingType = apps.get_model("meetings", "MeetingType")
    for order, (code, name) in enumerate(TYPES, start=1):
        MeetingType.objects.get_or_create(code=code, defaults={"name": name, "sort_order": order})


def unseed(apps, schema_editor):
    apps.get_model("meetings", "MeetingType").objects.filter(code__in=[c for c, _ in TYPES]).delete()


class Migration(migrations.Migration):
    dependencies = [("meetings", "0001_initial")]
    operations = [migrations.RunPython(seed, unseed)]
