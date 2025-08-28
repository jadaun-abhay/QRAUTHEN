from django.db.models.manager import BaseManager

from apps.core.enums import Status

# Write your managers here


class DeleteStatusManager(BaseManager):
    def get_queryset(self):
        return super().get_queryset().exclude(status=Status.DELETED)
