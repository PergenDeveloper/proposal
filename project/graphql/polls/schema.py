import graphene

from ...polls.models import Question
from ..polls.types import QuestionType
from .mutations import (
    QuestionCreate, 
    QuestionUpdate, 
    QuestionDelete,
    ChoiceCreate,
    ChoiceUpdate,
    ChoiceDelete
)



class PollsQueries(graphene.ObjectType):
    questions = graphene.List(
        QuestionType,
        description="List of all tax rates available from tax gateway."
    )

    def resolve_questions(self, info):
        return Question.objects.all()


class PollsMutations(graphene.ObjectType):
    question_create = QuestionCreate.Field()
    question_update = QuestionUpdate.Field()
    question_delete = QuestionDelete.Field()
    choice_create = ChoiceCreate.Field()
    choice_update = ChoiceUpdate.Field()
    choice_delete = ChoiceDelete.Field()