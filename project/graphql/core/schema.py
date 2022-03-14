import graphene

from .mutations import FileUpload


class CoreQueries(graphene.ObjectType):
    tax_types = graphene.Int(
        description="List of all tax rates available from tax gateway."
    )

    def resolve_tax_types(self, info):
        return 0


class CoreMutations(graphene.ObjectType):
    file_upload = FileUpload.Field()