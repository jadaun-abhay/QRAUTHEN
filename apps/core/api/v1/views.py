import base64
from datetime import datetime
import uuid6
import time
from typing import Dict
import asyncio
from django.contrib.auth import authenticate, login, logout
from django.http import StreamingHttpResponse
from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
)
from drf_spectacular.types import OpenApiTypes
from rest_framework.views import APIView
from base.api.v1.views import BaseAV
from base.api.v1.decorators import extend_schema_response

from apps.core.api.v1.serializers import LoginSerializer, QRSerializer
from apps.core.models import User, UserToken
from apps.core.functions import generate_new_token, generate_qr_code
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
        print(request.user)
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
        print(auth_data)
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


class QRAuthAV(BaseAV):
    "QR Management API View"

    def get_instance(self, uuid):
        instance = UserToken.objects.filter(uuid=uuid).first()
        print("instance_id", instance.id)
        return instance

    def get_verification_status(self, uuid, fields=None, exclude=None):
        start_time = datetime.now()
        status = True
        while status:
            current_time = datetime.now()
            difference = current_time - start_time
            if int(difference.total_seconds()) == 30:
                # New QR generation
                data = {
                    "token": "",
                }
                fields = (
                    "uuid",
                    "token",
                    "path",
                )
                exclude = None
                serializer = QRSerializer(
                    data=data,
                    fields=fields,
                    exclude=exclude,
                )
                if serializer.is_valid():
                    serializer.save()
                    yield serializer.data
                    continue

            instance = self.get_instance(uuid=uuid)
            serializer = QRSerializer(
                instance,
                fields=fields,
                exclude=exclude,
            )
            if instance.verification_status:
                yield serializer.data
                status = False
            else:
                yield serializer.data

    def get(self, request):
        params = request.query_params
        data = request.data

        fields = data.pop(
            "fields",
            (
                "uuid",
                "verification_status",
            ),
        )
        exclude = data.pop("exclude", ())

        uuid = params.get("uuid")
        print("uuid")

        verification_response = self.get_verification_status(uuid=uuid)
        print("verification_status", verification_response)
        response = StreamingHttpResponse(
            verification_response,
            status=status.HTTP_200_OK,
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        return response

    def post(self, request):
        data = request.data

        fields = data.pop(
            "fields",
            (
                "uuid",
                "token",
                "path",
            ),
        )
        exclude = data.pop("exclude", ())

        data = {
            "token": "unimportant",
        }

        serializer = QRSerializer(
            data=data,
            fields=fields,
            exclude=exclude,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.validated_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request):  # TODO: Mobile scan request
        data = request.data
        fields = data.pop("fields", ("uuid", "verification_status", "uid"))
        exclude = data.pop("exclude", ())

        data.update(
            {
                "uid": request.user.uuid,
            },
        )
        instane = self.get_instance(uuid=data.get("uuid"))
        # serializer

    
class QRStreamView(APIView):
    def event_stream(self):
        for i in range(3):
            uid = uuid6.uuid6()
            token = generate_new_token(uuid=uid)
            qr_code = generate_qr_code(uuid=uid, token=token)
            yield qr_code
            time.sleep(30)  

    def get(self, request, *args, **kwargs):
        return StreamingHttpResponse(
            self.event_stream(),
            content_type="image/svg+xml"
        )