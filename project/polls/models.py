from django.db import models

from ..core.permissions import ChoicePermissions, QuestionPermissions
from ..core.models import SimpleModel


class Question(SimpleModel):
    question_text = models.CharField(max_length=200)

    class Meta:
        permissions = (
            (
                QuestionPermissions.MANAGE_QUESTIONS.codename,
                "Manage questions.",
            ),
        )


class Choice(SimpleModel):
    question = models.ForeignKey(
        Question,
        related_name="choices",
        on_delete=models.CASCADE
    )
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)

    class Meta:
        permissions = (
            (
                ChoicePermissions.MANAGE_CHOICES.codename,
                "Manage choices.",
            ),
        )