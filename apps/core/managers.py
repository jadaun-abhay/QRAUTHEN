from django.db.models import Manager

from apps.core.enums import Status

# Write your managers here


class DeleteStatusManager(Manager):
    def get_queryset(self):
        return super().get_queryset().exclude(status=Status.DELETED)
