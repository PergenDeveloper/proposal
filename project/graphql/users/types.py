import graphene

from ...users import models
from ..core.types.model import ModelObjectType


class UserType(ModelObjectType):
    id = graphene.UUID(required=True)
    first_name = graphene.String()
    last_name = graphene.String()
    email = graphene.String()
    created = graphene.DateTime()

    class Meta:
        description = "Represents an user."
        model = models.User
