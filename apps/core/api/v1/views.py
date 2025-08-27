import base64

from typing import Dict

from django.contrib.auth import authenticate, login, logout

from rest_framework import status
from rest_framework.response import Response

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from base.api.v1.views import BaseAV
from base.api.v1.decorators import extend_schema_response

from apps.core.api.v1.serializers import LoginSerializer
from apps.core.models import User

# Write your views here


class LoginAV(BaseAV):
    "Login/Logout API View"

    authentication = {
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
                        description="",
                    )
                ],
            )
        ]
    )
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

    def delete(self, request):
        logout(request)
        response = {
            "msg": "Logout successfull.",
        }
        return Response(response, status=status.HTTP_200_OK)
