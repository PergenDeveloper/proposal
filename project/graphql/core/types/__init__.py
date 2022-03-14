
from urllib.parse import urljoin
from django.conf import settings
import graphene


class Upload(graphene.types.Scalar):
    class Meta:
        description = (
            "Variables of this type must be set to null in mutations. They will be "
            "replaced with a filename from a following multipart part containing "
            "a binary file. "
            "See: https://github.com/jaydenseric/graphql-multipart-request-spec."
        )

    @staticmethod
    def serialize(value):
        return value

    @staticmethod
    def parse_literal(node):
        return node

    @staticmethod
    def parse_value(value):
        return value


class File(graphene.ObjectType):
    url = graphene.String(required=True, description="The URL of the file.")
    content_type = graphene.String(
        required=False, description="Content type of the file."
    )

    @staticmethod
    def resolve_url(root, info):
        return info.context.build_absolute_uri(urljoin(settings.MEDIA_URL, root.url))