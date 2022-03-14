
import graphene

from ..enums import (
    ChoiceErrorCode, 
    QuestionErrorCode,
    UploadErrorCode,
    UserErrorCode,
)


class Error(graphene.ObjectType):
    field = graphene.String(
        description=(
            "Name of a field that caused the error. A value of `null` indicates that "
            "the error isn't associated with a particular field."
        ),
        required=False,
    )
    message = graphene.String(description="The error message.")


class UploadError(Error):
    code = UploadErrorCode(description="The error code.", required=True)


class QuestionError(Error):
    code = QuestionErrorCode(description="The error code.", required=True)


class ChoiceError(Error):
    code = ChoiceErrorCode(description="The error code.", required=True)

class UserError(Error):
    code = UserErrorCode(description="The error code.", required=True)