import base64
import io
import jwt
import qrcode
import qrcode.image.svg
import uuid6

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
    path = "media/{0}.svg".format(uuid)
    qr.save(path)
    return path


def generate_cookie_value(action, message=None):
    def encode():
        unique_string = str(uuid6.uuid6())
        string_bytes = unique_string.encode("ascii")
        base64_bytes = base64.b64encode(string_bytes)
        encoded = base64_bytes.decode("ascii")
        return encoded

    def decode():
        encoded_message = message
        message_bytes = encoded_message.encode("ascii")
        base64_bytes = base64.b64decode(message_bytes)
        decoded = base64_bytes.decode("ascii")
        return decoded

    if action == "encode":
        return encode()
    else:
        return decode()
