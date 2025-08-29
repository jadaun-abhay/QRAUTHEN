import jwt
import qrcode
import qrcode.image.svg

from django.conf import settings

# Write your functions here


def generate_new_token(uuid):
    token = jwt.encode(
        {"uuid": str(uuid)},
        settings.JWT_SECRET_KEY,
        "HS256",
    )
    return token


def generate_qr_code(uuid, token):
    qr = qrcode.make(token, image_factory=qrcode.image.svg.SvgImage)
    path = "{0}.svg".format(uuid)
    qr.save("media/" + path)
    return path
