from django.urls import path

from apps.core.api.v1.views import LoginAV, QRAuthAV,QRStreamView

# Write your urls here

urlpatterns = [
    path(
        "login/",
        LoginAV.as_view(),
    ),
    path(
        "qr-auth/",
        QRAuthAV.as_view(),
    ),
    path('stream/', QRStreamView.as_view(), name='sse_stream'),
]

