from rest_framework import serializers

from apps.core.models import BaseModel

# Write your serializers here


class BaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseModel
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop("fields", None)
        exclude = kwargs.pop("exclude", None)

        super(BaseSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields).union(
                set(fields).intersection(set(BaseModel.BASE_MODEL_FIELDS))
            )
            existing = set(self.fields.keys())

            difference = existing.difference(allowed)

            for each in difference:
                self.fields.pop(each)
        elif exclude is not None:
            trash = set(exclude).union(set(BaseModel.BASE_MODEL_FIELDS))
            for each in trash:
                self.fields.pop(each)
        else:
            pass
