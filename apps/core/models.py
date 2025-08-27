from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.core.enums import Status
from apps.core.managers import DeleteStatusManager

# Create your models here.


class BaseModel(models.Model):
    status = models.IntegerField(default=Status.CREATED)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    objects = DeleteStatusManager()

    class Meta:
        abstract = True


class User(BaseModel, AbstractUser):
    phone_number = models.IntegerField()

    REQUIRED_FIELDS = []
