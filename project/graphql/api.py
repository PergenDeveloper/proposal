import graphene

from .core.schema import CoreQueries, CoreMutations
from .polls.schema import PollsQueries, PollsMutations
from .users.schema import UsersQueries, UsersMutation

class Query(
    CoreQueries,
    PollsQueries,
    UsersQueries
):
    pass

class Mutation(
    CoreMutations,
    PollsMutations,
    UsersMutation
):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)