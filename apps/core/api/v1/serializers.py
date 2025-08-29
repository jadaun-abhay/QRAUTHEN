import os

from django.conf import settings

from rest_framework import serializers

from base.api.v1.serializers import BaseSerializer

from apps.core.models import User, UserToken
from apps.core.functions import generate_new_token, generate_qr_code

# Write your serializers here


class LoginSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = "__all__"


class QRSerializer(BaseSerializer):
    path = serializers.FileField(use_url=True)

    class Meta:
        model = UserToken
        fields = "__all__"

    def validate(self, data):
        token = data.get("token")
        if token == "":
            instance = UserToken.objects.create(**data)
            data.update(
                {
                    "uuid": instance.uuid,
                }
            )
            return data
        return data

    def save(self):
        uuid = self.validated_data.get("uuid")
        token = generate_new_token(uuid=uuid)
        path = generate_qr_code(
            uuid=uuid,
            token=token,
        )
        path = os.path.join(
            settings.MEDIA_ROOT,
            path,
        )
        self.validated_data.update(
            {
                "path": path,
            }
        )
        return UserToken.objects.update_or_create(
            uuid=uuid, defaults=self.validated_data
        )
