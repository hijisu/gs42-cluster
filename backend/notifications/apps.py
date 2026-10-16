from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    name = "notifications"

    def ready(self) -> None:
        from notifications.interfaces.wiring import register

        register()
