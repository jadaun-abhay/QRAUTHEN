from rest_framework import serializers

from base.api.v1.serializers import BaseSerializer

from apps.core.models import User

# Write your serializers here


class LoginSerializer(BaseSerializer):
    class Meta:
        model = User
        fields = "__all__"
