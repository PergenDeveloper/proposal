from datetime import timedelta, datetime

from django.forms import ValidationError
import jwt
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.handlers.wsgi import WSGIRequest

from ..users.error_codes import UserErrorCodes

from ..users.models import User

DEFAULT_AUTH_HEADER = "HTTP_AUTHORIZATION"
AUTH_HEADER_PREFIXES = ["JWT", "BEARER"]

JWT_OWNER_NAME = "your-project-name"  # for security read it from env
JWT_OWNER_FIELD = "owner"

JWT_ACCESS_TYPE = "access"
JWT_REFRESH_TYPE = "refresh"


def jwt_base_payload(
    exp_delta: Optional[timedelta], token_owner: str
) -> Dict[str, Any]:
    utc_now = datetime.utcnow()
    payload = {"iat": utc_now, JWT_OWNER_FIELD: token_owner}
    if exp_delta:
        payload["exp"] = utc_now + exp_delta
    return payload


def jwt_user_payload(
    user: User,
    token_type: str,
    exp_delta: Optional[timedelta],
    token_owner: str = JWT_OWNER_NAME,
) -> Dict[str, Any]:

    payload = jwt_base_payload(exp_delta, token_owner)
    payload.update(
        {
            "token": user.jwt_token_key,
            "email": user.email,
            "type": token_type,
            "user_id": str(user.id),
            "is_staff": user.is_staff,
        }
    )
    return payload


def jwt_encode(payload: Dict[str, Any]) -> str:
    token = jwt.encode(
        payload, 
        settings.SECRET_KEY, 
        algorithm="HS256",
    )
    return token


def jwt_decode(token: str) -> Dict[str, Any]:
    payload = jwt.decode(
        token,
        settings.SECRET_KEY, 
        algorithms=["HS256"]
    )
    return payload


def get_payload(token):
    try:
        payload = jwt_decode(token)
    except jwt.ExpiredSignatureError:
        raise ValidationError(
            "Signature has expired.", code=UserErrorCodes.JWT_SIGNATURE_EXPIRED.value
        )
    except jwt.DecodeError:
        raise ValidationError(
            "Error decoding signature.", code=UserErrorCodes.JWT_DECODE_ERROR.value
        )
    except jwt.InvalidTokenError:
        raise ValidationError(
            "Invalid token.", code=UserErrorCodes.JWT_INVALID_TOKEN.value
        )
    return payload


def get_token_from_request(request: WSGIRequest) -> Optional[str]:
    auth_token = None

    auth = request.META.get(DEFAULT_AUTH_HEADER, "").split(maxsplit=1)
    if len(auth) == 2 and auth[0].upper() in AUTH_HEADER_PREFIXES:
        auth_token = auth[1]
    return auth_token


def is_custom_token(token: str) -> bool:
    """Confirm that token was generated by the app not by original plugin."""
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
    except jwt.PyJWTError:
        return False
    owner = payload.get(JWT_OWNER_FIELD)
    if not owner or owner != JWT_OWNER_NAME:
        return False
    return True


def get_user_from_payload(payload: Dict[str, Any]) -> Optional[User]:
    user = User.objects.filter(email=payload["email"], is_active=True).first()
    user_jwt_token = payload.get("token")
    if not user_jwt_token or not user:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    if user.jwt_token_key != user_jwt_token:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    return user


def get_user_from_access_payload(payload: dict) -> Optional[User]:
    jwt_type = payload.get("type")
    if jwt_type not in [JWT_ACCESS_TYPE, ]:
        raise jwt.InvalidTokenError(
            "Invalid token. Create new one by using tokenCreate mutation."
        )
    user = get_user_from_payload(payload)
    return user


def get_user_from_access_token(token: str) -> Optional[User]:
    if not is_custom_token(token):
        return None
    payload = get_payload(token)
    return get_user_from_access_payload(payload)


def create_token(payload: Dict[str, Any], exp_delta: timedelta) -> str:
    payload.update(jwt_base_payload(exp_delta, token_owner=JWT_OWNER_NAME))
    return jwt_encode(payload)


def create_access_token(user: User, allow_exp=True) -> str:
    payload = jwt_user_payload(
        user, 
        JWT_ACCESS_TYPE,
        exp_delta=timedelta(
            minutes=settings.JWT_SIGNATURE_ACCESS_EXPIRED_TIME
        ) if allow_exp else None
    )
    return jwt_encode(payload)


def create_refresh_token(user: User) -> str:
    payload = jwt_user_payload(
        user, 
        JWT_REFRESH_TYPE, 
        exp_delta=timedelta(
            minutes=settings.JWT_SIGNATURE_REFRESH_EXPIRED_TIME
        )
    )
    return jwt_encode(payload)

