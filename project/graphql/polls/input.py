import graphene


class QuestionInput(graphene.InputObjectType):
    question_text = graphene.String(
        required=True
    )


class ChoiceCreateInput(graphene.InputObjectType):
    question = graphene.UUID(
       required=True
    )
    choice_text = graphene.String(required=True)
    votes = graphene.Int()


class ChoiceUpdateInput(ChoiceCreateInput):
    question = graphene.UUID()
    choice_text = graphene.String()