import base64
import time
import json
import uuid6

from datetime import datetime

from typing import Dict

from django.conf import settings
from django.contrib.auth import authenticate, login, logout

from drf_sse import SSEMixin, SSEResponse

from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    inline_serializer,
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
            "message": "Invalid Credentials.",
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
        "get": False,
        "post": False,
    }

    def get_instance(self, uuid, token=None, cookie=None):
        if token is None:
            instance = UserToken.objects.filter(uuid=uuid).first()
            return instance
        elif cookie is None:
            instance = UserToken.objects.filter(token=token).first()
        else:
            instance = UserToken.objects.filter(cookie=cookie).first()
        return instance

    @extend_schema_response(
        type=inline_serializer(
            name="DeviceIdentificationSerializer",
            fields={
                "uuid": serializers.UUIDField(),
                "path": serializers.StringRelatedField(required=False),
                "verification_status": serializers.BooleanField(required=False),
            },
        )
    )
    def get(self, request):
        "API View to send QR and start a sever sent event."

        def get_sse_details(uuid, token, cookie):
            data = {
                "uuid": uuid,
                "token": token,
                "cookie": cookie,
            }
            uuid = None

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

                print("total_seconds", total_seconds, uuid)
                if uuid is None and total_seconds != settings.QR_REGENRATION_TIME:
                    # New QR generation

                    fields = (
                        "uuid",
                        "path",
                        "verification_status",
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
                        serializer.validated_data["uuid"] = str(
                            serializer.validated_data.get("uuid")
                        )
                        yield json.dumps(serializer.data)
                        print("***in loop checking cookies", request.COOKIES)

                else:
                    instance = self.get_instance(uuid=uuid)
                    fields = (
                        "uuid",
                        "verification_status",
                    )
                    exclude = None
                    serializer = QRSerializer(
                        instance,
                        fields=fields,
                        exclude=exclude,
                    )
                    if instance.verification_status:
                        yield json.dumps(serializer.data)
                        status = False
                        response.delete_cookie("identification")
                    else:
                        yield json.dumps(serializer.data)
                        print("***?in loop checking cookies", request.COOKIES)
                    if total_seconds >= settings.QR_REGENRATION_TIME:
                        uuid = None
                        data["uuid"] = uuid6.uuid6()
                        data["token"] = generate_new_token(data.get("uuid"))
                        generate_qr_code(uuid=data["uuid"], token=data["token"])
                        total_seconds = 0
                        start_time = datetime.now()
                        lap += 1
                time.sleep(5)

        uuid = uuid6.uuid6()
        cookie_value = generate_cookie_value("encode", uuid=uuid)
        token = generate_new_token(uuid=uuid)
        generate_qr_code(uuid=uuid, token=token)

        response = SSEResponse(
            get_sse_details(
                uuid=uuid,
                token=token,
                cookie=cookie_value,
            ),
        )
        response.set_cookie(
            "identification",
            cookie_value,
            samesite="Lax",
        )

        return response

    @extend_schema_response(CustomMessageSerializer)
    def post(self, request):
        "API View to login the system after the server sent event has been closed."

        data = request.data
        print("PRINCE BODY", data)

        uuid = data.get("uuid")
        print("POST prince", uuid)
        instance = self.get_instance(uuid=uuid)
        if instance.verification_status is False:
            response = {
                "msg": "Not verified user.",
            }
            return Response(response, status=status.HTTP_200_OK)
        login(request, instance.user)
        response = {
            "msg": "Login successful through QR.",
        }
        return Response(response, status=status.HTTP_201_CREATED)

    @extend_schema(
        request={
            "application/json": {
                "type": "object",
                "required": [
                    "scanned_token",
                ],
                "properties": {
                    "scanned_token": {
                        "type": "string",
                        "format": "uuid",
                        "description": "Token scanned after decoding QR code.",
                    },
                },
            }
        }
    )
    @extend_schema_response(CustomMessageSerializer)
    def put(self, request):
        data = request.data
        fields = data.pop("fields", ("token", "verification_status", "uid"))
        exclude = data.pop("exclude", ())

        token = data.pop("scanned_token", None)
        if token is None:
            response = {
                "message": "Token not received",
            }
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        data.update(
            {
                "uid": request.user.uuid,
                "token": token,
            },
        )
        instance = self.get_instance(uuid=None, token=token)
        print("instance_PUT", instance)
        data.update(
            {
                "uuid": instance.uuid,
                "verification_status": True,
            },
        )
        serializer = QRSerializer(
            instance,
            data=data,
            fields=fields,
            exclude=exclude,
        )

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            response = {
                "msg": "Status saved.",
            }
            return Response(response, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
