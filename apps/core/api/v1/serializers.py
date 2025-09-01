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


class UserCustomRelatedField(serializers.RelatedField):
    def to_representation(self, value):
        return User.objects.filter(id=value).first().uuid

    def to_internal_value(self, uuid):
        return User.objects.filter(uuid=uuid).first().id


class QRSerializer(BaseSerializer):
    uid = UserCustomRelatedField(
        source="user_id",
        queryset=User.objects.all(),
        allow_null=True,
    )

    class Meta:
        model = UserToken
        fields = "__all__"

    def validate(self, data):
        token = data.get("token")
        if token is None:
            instance = UserToken.objects.create(**self.initial_data)
            data.update(
                {
                    "uuid": instance.uuid,
                }
            )
            return data
        else:
            data.update(
                {
                    "uuid": self.instance.uuid,
                }
            )
        return data

    def update(self, instance, validated_data):
        instance.verification_status = validated_data.get(
            "validated_data",
            instance.verification_status,
        )
        instance.user_id = validated_data.get(
            "uid",
            instance.user_id,
        )
        return instance

    def save(self):
        uuid = self.validated_data.get("uuid")
        token = generate_new_token(uuid=uuid)
        cookie = token
        path = generate_qr_code(
            uuid=uuid,
            token=token,
        )
        path = os.path.join(
            path,
        )
        self.validated_data.update({"token": token, "path": path, "cookie": cookie})
        if uuid is None:
            return UserToken.objects.create(**self.validated_data)
        return UserToken.objects.update_or_create(
            uuid=uuid, defaults=self.validated_data
        )[0]
