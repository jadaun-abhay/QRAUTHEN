import uuid6

from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

from apps.core.enums import Status
from apps.core.managers import DeleteStatusManager

# Create your models here.


class BaseModel(models.Model):
    BASE_MODEL_FIELDS = (
        "id",
        "status",
        "created_at",
        "updated_at",
    )

    uuid = models.UUIDField(default=uuid6.uuid6)
    status = models.IntegerField(default=Status.CREATED)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    objects = DeleteStatusManager()

    class Meta:
        abstract = True


class User(BaseModel, AbstractUser):
    USER_MODEL_FIELDS = BaseModel.BASE_MODEL_FIELDS + (
        "is_superuser",
        "last_login",
        "is_staff",
        "is_active",
        "date_joined",
        "groups",
        "user_permissions",
        "password",
    )

    phone_number = models.BigIntegerField()

    REQUIRED_FIELDS = []

    objects = UserManager()


class UserToken(BaseModel):
    token = models.CharField(max_length=170, null=True)
    path = models.FileField(null=True)
    verification_status = models.BooleanField(default=False)
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        related_name="tokens",
    )
