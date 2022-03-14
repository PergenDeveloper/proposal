import graphene

from ...polls import models
from ..core.types.model import ModelObjectType


class QuestionType(ModelObjectType):
    id = graphene.UUID(required=True)
    question_text = graphene.String()
    choices = graphene.List(
        lambda: ChoiceType, 
        required=True
    )
    created = graphene.DateTime()

    class Meta:
        description = "Represents an question."
        model = models.Question

    def resolve_choices(self, info, **kwargs):
        if hasattr(self, 'choices'):
            return self.choices.all()
        return []


class ChoiceType(ModelObjectType):
    id = graphene.UUID(required=True)
    question = graphene.Field(
        QuestionType,
        required=True,
        description="Represents question object."
    )
    choice_text = graphene.String()
    votes = graphene.Int()
    created = graphene.DateTime()

    class Meta:
        description = "Represents an choice."
        model = models.Choice