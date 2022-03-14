import graphene

from ...core.permissions import ChoicePermissions, QuestionPermissions
from ...polls import models
from ..core.types.errors import ChoiceError, QuestionError
from ..core.mutations import ModelMutation, ModelDeleteMutation
from .types import ChoiceType, QuestionType
from .input import ChoiceCreateInput, ChoiceUpdateInput, QuestionInput


class QuestionCreate(ModelMutation):
    class Arguments:
        input = QuestionInput(
            required=True,
            description="Fields requiered to create a question."
        )

    class Meta:
        description = "Creates a new question."
        model = models.Question
        object_type = QuestionType
        permissions = (QuestionPermissions.MANAGE_QUESTIONS,)
        error_type_class = QuestionError


class QuestionUpdate(ModelMutation):
    class Arguments:
        id = graphene.UUID(required=True)
        input = QuestionInput(
            required=True,
            description="Fields requiered to update a question."
        )

    class Meta:
        description = "Updates a question."
        model = models.Question
        object_type = QuestionType
        permissions = (QuestionPermissions.MANAGE_QUESTIONS,)
        error_type_class = QuestionError


class QuestionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.UUID(required=True)

    class Meta:
        description = "Deletes a question."
        model = models.Question
        object_type = QuestionType
        permissions = (QuestionPermissions.MANAGE_QUESTIONS,)
        error_type_class = QuestionError


class ChoiceCreate(ModelMutation):
    class Arguments:
        input = ChoiceCreateInput(
            required=True,
            description="Fields requiered to create a choice."
        )

    class Meta:
        description = "Creates a choice."
        model = models.Choice
        object_type = ChoiceType
        permissions = (ChoicePermissions.MANAGE_CHOICES,)
        error_type_class = ChoiceError


class ChoiceUpdate(ModelMutation):
    class Arguments:
        id = graphene.UUID(required=True)
        input = ChoiceUpdateInput(
            required=True,
            description="Fields requiered to update a choice."
        )

    class Meta:
        description = "Updates a choice."
        model = models.Choice
        object_type = ChoiceType
        permissions = (ChoicePermissions.MANAGE_CHOICES,)
        error_type_class = ChoiceError


class ChoiceDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.UUID(required=True)

    class Meta:
        description = "Deletes a choice."
        model = models.Choice
        object_type = ChoiceType
        permissions = (ChoicePermissions.MANAGE_CHOICES,)
        error_type_class = ChoiceError