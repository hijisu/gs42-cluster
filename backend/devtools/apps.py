from django.apps import AppConfig


class DevtoolsConfig(AppConfig):
    """개발·시연 보조 명령 모음(운영 로직 없음). 명령은 모두 DJANGO_DEBUG=true 에서만 동작한다."""

    name = "devtools"
