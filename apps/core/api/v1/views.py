import base64
from datetime import datetime
import time
import uuid6

from typing import Dict

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.files import File

from drf_sse import SSEMixin, SSEResponse

from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes

from base.api.v1.views import BaseAV
from base.api.v1.decorators import extend_schema_response

from apps.core.api.v1.serializers import LoginSerializer, QRSerializer
from apps.core.models import User, UserToken
from apps.core.functions import (
    generate_new_token,
    generate_cookie_value,
    generate_qr_code,
)
from apps.core.schema import CustomMessageSerializer

# Write your views here


class LoginAV(BaseAV):
    "Login/Logout API View"

    authentication = {
        "get": True,
        "post": False,
    }

    def decrypt_auth(self, meta_info) -> None | Dict:
        header, data = meta_info.split(" ")
        if header != "Basic":
            return None
        decrypted_auth = base64.b64decode(data).decode("utf-8")
        credentials = decrypted_auth.split(":")
        return {
            "username": credentials[0],
            "password": credentials[1],
        }

    @extend_schema_response(type=LoginSerializer(exclude=User.USER_MODEL_FIELDS))
    def get(self, request):
        serializer = LoginSerializer(
            instance=request.user,
            exclude=User.USER_MODEL_FIELDS,
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="Authorization",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                required=True,
                examples=[
                    OpenApiExample(
                        name="User Authentication",
                        value="Basic ZXJwQGtpZXQuZWR1OkBlcnA=",
                        summary="base64 encoded credentials are required",
                        description="username:password This string must be encoded in base64 format.",
                    )
                ],
            )
        ]
    )
    @extend_schema_response(type=CustomMessageSerializer)
    def post(self, request):
        auth_data = request.META.get("HTTP_AUTHORIZATION")
        credentials = self.decrypt_auth(auth_data)
        user = authenticate(request, **credentials)
        if user is not None:
            login(request, user)
            response = {
                "msg": "Login Successfull.",
            }
            return Response(response, status=status.HTTP_201_CREATED)
        response = {
            "msg": "Invalid Credentials.",
        }
        return Response(response, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema_response(type=CustomMessageSerializer)
    def delete(self, request):
        logout(request)
        response = {
            "msg": "Logout successfull.",
        }
        return Response(response, status=status.HTTP_200_OK)


class QRAuthAV(SSEMixin, BaseAV):
    "QR Management API View"

    authentication = {
        "post": False,
    }

    user = None

    def get_instance(self, uuid, token=None):
        if token is None:
            instance = UserToken.objects.filter(uuid=uuid).first()
            return instance
        instance = UserToken.objects.filter(token=token).first()
        return instance

    def get(self, request):
        pass

    def post(self, request):

        def get_sse_details(uuid):
            start_time = datetime.now()
            status = True
            lap = 0

            while status:
                current_time = datetime.now()
                difference = current_time - start_time
                total_seconds = int(difference.total_seconds())

                if lap == 3:
                    response.delete_cookie("identification")
                    break

                if uuid is None and total_seconds != settings.QR_REGENRATION_TIME:
                    # New QR generation
                    data = {
                        "token": "",
                    }

                    fields = (
                        "uuid",
                        "path",
                    )
                    exclude = None
                    serializer = QRSerializer(
                        data=data,
                        fields=fields,
                        exclude=exclude,
                    )
                    if serializer.is_valid():
                        instance = serializer.save()
                        uuid = instance.uuid
                        del serializer.validated_data["cookie"]
                        yield serializer.validated_data

                else:
                    instance = self.get_instance(uuid=uuid)
                    fields = (
                        "uuid",
                        "verification_status",
                    )
                    serializer = QRSerializer(
                        instance,
                        fields=fields,
                        exclude=exclude,
                    )
                    if instance.verification_status:
                        yield serializer.data
                        print("Now login")
                        login(request, instance.user)
                        status = False
                    else:
                        yield serializer.data
                    if total_seconds >= settings.QR_REGENRATION_TIME:
                        uuid = None
                        total_seconds = 0
                        start_time = datetime.now()
                        lap += 1
                time.sleep(5)

        response = SSEResponse(
            get_sse_details(uuid=None),
        )
        response.set_cookie(
            "identification",
            generate_cookie_value("encode"),
        )

        return response

    def put(self, request):
        data = request.data
        fields = data.pop("fields", ("token", "verification_status", "uid"))
        exclude = data.pop("exclude", ())

        token = data.pop("scanned_token", None)
        data.update(
            {
                "uid": request.user.uuid,
                "token": token,
            },
        )
        instance = self.get_instance(uuid=None, token=token)
        data.update(
            {
                "uuid": instance.uuid,
                "verification_status": True,
            },
        )
        print(data)
        serializer = QRSerializer(
            instance,
            data,
            fields=fields,
            exclude=exclude,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
