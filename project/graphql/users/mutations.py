from typing import Optional

from django.contrib.auth import password_validation
from django.forms import ValidationError
from django.utils import timezone
import graphene

from ...core.jwt import JWT_REFRESH_TYPE, create_access_token, create_refresh_token, get_payload, get_user_from_payload
from ...users import models
from ...users.error_codes import UserErrorCodes 
from ..core.mutations import BaseMutation, ModelMutation
from ..core.types.errors import UserError
from .types import UserType
from .inputs import AccountRegisterInput


class TokenCreate(BaseMutation):
    user = graphene.Field(UserType)
    token = graphene.String(description="JWT token, required to authenticate.")
    refresh_token = graphene.String(
        description="JWT refresh token, required to re-generate access token."
    )

    class Arguments:
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    class Meta:
        description = "Checks credencials for login."
        permissions = ()
        error_type_class = UserError

    @classmethod
    def _retrieve_user_from_credentials(cls, email, password) -> Optional[models.User]:
        user = models.User.objects.filter(email=email).first()
        if user and user.check_password(password):
            return user
        return None

    @classmethod
    def get_user(cls, _info, data):
        user = cls._retrieve_user_from_credentials(data["email"], data["password"])
        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Please, enter valid credentials.",
                        code=UserErrorCodes.INVALID_CREDENTIALS.value,
                    )
                }
            )

        if not user.is_active and user.last_login:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "Account inactive.",
                        code=UserErrorCodes.INACTIVE.value,
                    )
                }
            )
        return user

    @classmethod
    def perform_mutation(cls, _, info, **data):
        user = cls.get_user(info, data)
        access_token = create_access_token(user)
        refresh_token = create_refresh_token(user)
        user.last_login = timezone.now()
        user.save(update_fields=["last_login", "modified"])

        return cls(
            errors=[],
            user=user,
            token=access_token,
            refresh_token=refresh_token,
        )


class TokenRefresh(BaseMutation):
    """Mutation that refresh user token and returns token and user data."""

    token = graphene.String(description="JWT token, required to authenticate.")
    user = graphene.Field(UserType, description="A user instance.")

    class Arguments:
        refresh_token = graphene.String(required=True, description="Refresh token.")

    class Meta:
        description = "Refresh JWT token."
        error_type_class = UserError

    @classmethod
    def get_refresh_token_payload(cls, refresh_token):
        try:
            payload = get_payload(refresh_token)
        except ValidationError as e:
            raise ValidationError({"refreshToken": e})
        return payload

    @classmethod
    def get_refresh_token(cls, info, data):
        refresh_token = data.get("refresh_token")
        return refresh_token

    @classmethod
    def clean_refresh_token(cls, refresh_token):
        if not refresh_token:
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Missing refreshToken",
                        code=UserErrorCodes.JWT_MISSING_TOKEN.value,
                    )
                }
            )
        payload = cls.get_refresh_token_payload(refresh_token)
        if payload["type"] != JWT_REFRESH_TYPE:
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Incorrect refreshToken",
                        code=UserErrorCodes.JWT_INVALID_TOKEN.value,
                    )
                }
            )
        return payload

    @classmethod
    def get_user(cls, payload):
        try:
            user = get_user_from_payload(payload)
        except ValidationError as e:
            raise ValidationError({"refresh_token": e})
        return user

    @classmethod
    def perform_mutation(cls, root, info, **data):
        refresh_token = cls.get_refresh_token(info, data)
        payload = cls.clean_refresh_token(refresh_token)
        user = cls.get_user(payload)
        token = create_access_token(user)
        return cls(errors=[], user=user, token=token)


class AccountRegister(ModelMutation):
    class Arguments:
        input = AccountRegisterInput(
            description="Fields required to create an user.", required=True
        )

    class Meta:
        description = "Creates an user."
        model = models.User
        exclude = ["password"]
        object_type = UserType
        permissions = ()
        error_type_class = UserError

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        password = data["password"]
        data['email'] = data.get("email").lower()
        
        try:
            password_validation.validate_password(password, instance)
        except ValidationError as error:
            raise ValidationError({"password": error})

        return super().clean_input(info, instance, data, input_cls=None)

    @classmethod
    def save(cls, info, user, cleaned_input):
        password = cleaned_input["password"]
        user.set_password(password)
        user.save()

