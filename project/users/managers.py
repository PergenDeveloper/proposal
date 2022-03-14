#! -*- coding: utf-8 -*-
from typing import Any  # NOQA

from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db.models import Model, QuerySet


class UserManager(DjangoUserManager):
    def _create_user(
        self, email: str, password: str = None, **extra_fields: Any
    ) -> Model:
        """
        Creates and saves a User with the given email and password.
        """
        email = self.normalize_email(email.lower())
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(
        self, email: str, password: str = None, **extra_fields: Any
    ) -> Model:
        if not email:
            raise ValueError("Users must have an email address")
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_user_random_password(self, email: str, **extra_fields: Any) -> Model:
        if not email:
            raise ValueError("Users must have an email address")
        password = self.make_random_password()
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(
        self, email: str, password: str = None, **extra_fields: Any
    ) -> Model:
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username: str) -> Model:
        return self.get(**{self.model.USERNAME_FIELD + "__iexact": username})

    def filter_active(self) -> QuerySet:
        return self.exclude(is_active=False)
