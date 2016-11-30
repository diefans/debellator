from zope import interface


class IEvolvable(interface.Interface):

    """Define the possibility to evolve."""

    async def evolve(self, scope, remote, fallback=None):
        """Evolve remote by using scope."""


class IRemote(interface.Interface):

    """A remote."""