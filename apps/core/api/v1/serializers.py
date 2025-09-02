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

    path = serializers.SerializerMethodField("get_path")

    class Meta:
        model = UserToken
        fields = "__all__"

    def get_path(self, data):
        return "{0}.svg".format(data.get("uuid"))

    def validate(self, data):
        if self.instance is not None:
            return data
        return self.initial_data

    def save(self):
        if self.instance is not None:
            uuid = self.instance.uuid
        else:
            uuid = self.validated_data.get("uuid")
        if uuid is None:
            return UserToken.objects.create(**self.validated_data)
        return UserToken.objects.update_or_create(
            uuid=uuid, defaults=self.validated_data
        )[0]
