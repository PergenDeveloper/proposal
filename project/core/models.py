import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """
    An abstract class with id as UUID.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    class Meta:
        abstract = True


class SimpleModel(BaseModel):
    """
    An abstract base class model that provides:
    self-updating 'created' and 'modified' fields.
    """
    created = models.DateTimeField(
        verbose_name=_("created date"),
        null=True,
        auto_now_add=True,
    )
    modified = models.DateTimeField(
        verbose_name=_("modified date"), null=True, auto_now=True
    )

    class Meta:
        abstract = True
        ordering = ("-created",)