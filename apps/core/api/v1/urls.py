from django.urls import path

from apps.core.api.v1.views import LoginAV

# Write your urls here

urlpatterns = [
    path(
        "login/",
        LoginAV.as_view(),
    )
]
