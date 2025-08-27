from rest_framework.views import APIView

from base.api.v1.permissions import AccessAuthenticationPermission


# Write your views here


class BaseAV(APIView):
    authentication: dict | bool

    permission_classes = [
        AccessAuthenticationPermission,
    ]
