from enum import Enum


class BasePermissionEnum(Enum):
    @property
    def codename(self):
        return self.value.split(".")[1]

class QuestionPermissions(BasePermissionEnum):
    MANAGE_QUESTIONS = "question.manage_questions"


class ChoicePermissions(BasePermissionEnum):
    MANAGE_CHOICES = "choice.manage_choices"