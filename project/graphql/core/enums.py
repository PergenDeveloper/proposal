import graphene

from ...core.error_codes import UploadErrorCodes
from ...polls.error_codes import ChoiceErrorCodes, QuestionErrorCodes
from ...users.error_codes import UserErrorCodes


UploadErrorCode = graphene.Enum.from_enum(UploadErrorCodes)
QuestionErrorCode = graphene.Enum.from_enum(QuestionErrorCodes)
ChoiceErrorCode = graphene.Enum.from_enum(ChoiceErrorCodes)
UserErrorCode = graphene.Enum.from_enum(UserErrorCodes)