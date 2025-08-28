from rest_framework import serializers

from drf_spectacular.utils import inline_serializer

# Write your schema here

CustomMessageSerializer = inline_serializer(
    name="CustomMessageSerializer",
    fields={
        "msg": serializers.StringRelatedField(),
    },
)
