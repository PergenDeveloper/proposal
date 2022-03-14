import uuid
from typing import TYPE_CHECKING  # NOQA

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.translation import gettext_lazy as _
from ..core.models import SimpleModel
from .managers import UserManager


class User(AbstractBaseUser, SimpleModel, PermissionsMixin):
    """Description: Customized User Model"""

    first_name = models.CharField(
        verbose_name=_("first name"),
        max_length=30,
        blank=True,
        null=True,
    )
    last_name = models.CharField(
        verbose_name=_("last name"),
        max_length=30,
        blank=True,
        null=True,
    )
    phone = models.CharField(
        verbose_name=_("phone"), max_length=15, blank=True, null=True, unique=True
    )
    
    email = models.EmailField(
        verbose_name=_("email address"),
        unique=True,
    )
    email_confirmed = models.BooleanField(
        verbose_name=_("email confirmed"), default=False
    )
    is_staff = models.BooleanField(
        verbose_name=_("staff status"),
        default=False,
        help_text=_("Designates whether the user " "can log into this admin site."),
    )
    is_active = models.BooleanField(
        verbose_name=_("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as "
            "active. Unselect this instead of deleting accounts."
        ),
    )
    jwt_token_key = models.CharField(max_length=12, default=get_random_string)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    def get_full_name(self):
        # type: () -> str
        full_name = "%s %s" % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        # type: () -> str
        return self.first_name

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ("first_name", "last_name")
