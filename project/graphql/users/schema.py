import graphene
from django.utils import timezone

from graphql_jwt.decorators import login_required
from .mutations import (
    TokenCreate,
    TokenRefresh,
    AccountRegister
)
from .types import UserType


class UsersMutation(graphene.ObjectType):
    token_create = TokenCreate.Field()
    token_refresh = TokenRefresh.Field()
    account_register = AccountRegister.Field()


class UsersQueries(graphene.ObjectType):
    me = graphene.Field(UserType)

    @login_required
    def resolve_me(self, info):
        user = info.context.user
        return user
