from common.domain.errors import NotFoundError


class NotificationNotFound(NotFoundError):
    code = "notification_not_found"
